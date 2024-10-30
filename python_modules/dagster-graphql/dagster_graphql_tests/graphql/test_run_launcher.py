from typing import Any
from unittest.mock import patch

from dagster._core.test_utils import wait_for_runs_to_finish
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster_graphql.client.query import (
    LAUNCH_MULTIPLE_RUNS_MUTATION,
    LAUNCH_PIPELINE_EXECUTION_MUTATION,
)
from dagster_graphql.test.utils import execute_dagster_graphql, infer_job_selector

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    GraphQLContextVariant,
    make_graphql_context_test_suite,
)

RUN_QUERY = """
query RunQuery($runId: ID!) {
  pipelineRunOrError(runId: $runId) {
    __typename
    ... on Run {
      status
      stats {
        ... on RunStatsSnapshot {
          stepsSucceeded
        }
      }
      startTime
      endTime
    }
  }
}
"""


BaseTestSuite: Any = make_graphql_context_test_suite(
    context_variants=GraphQLContextVariant.all_executing_variants()
)
LaunchFailTestSuite: Any = make_graphql_context_test_suite(
    context_variants=GraphQLContextVariant.all_non_launchable_variants()
)
ReadOnlyTestSuite: Any = make_graphql_context_test_suite(
    context_variants=GraphQLContextVariant.all_readonly_variants()
)


class TestBasicLaunch(BaseTestSuite):
    def test_run_launcher(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "no_config_job")
        result = execute_dagster_graphql(
            context=graphql_context,
            query=LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={"executionParams": {"selector": selector, "mode": "default"}},
        )

        assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"
        assert result.data["launchPipelineExecution"]["run"]["status"] == "STARTING"

        run_id = result.data["launchPipelineExecution"]["run"]["runId"]

        wait_for_runs_to_finish(graphql_context.instance)

        result = execute_dagster_graphql(
            context=graphql_context, query=RUN_QUERY, variables={"runId": run_id}
        )
        assert result.data["pipelineRunOrError"]["__typename"] == "Run"
        assert result.data["pipelineRunOrError"]["status"] == "SUCCESS"

    def test_run_launcher_subset(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "more_complicated_config", ["noop_op"])
        result = execute_dagster_graphql(
            context=graphql_context,
            query=LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "mode": "default",
                }
            },
        )

        assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"
        assert result.data["launchPipelineExecution"]["run"]["status"] == "STARTING"

        run_id = result.data["launchPipelineExecution"]["run"]["runId"]

        wait_for_runs_to_finish(graphql_context.instance)

        result = execute_dagster_graphql(
            context=graphql_context, query=RUN_QUERY, variables={"runId": run_id}
        )
        assert result.data["pipelineRunOrError"]["__typename"] == "Run"
        assert result.data["pipelineRunOrError"]["status"] == "SUCCESS"
        assert result.data["pipelineRunOrError"]["stats"]["stepsSucceeded"] == 1


class TestMultipleLaunch(BaseTestSuite):
    def test_multiple_run_launcher_same_job(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "no_config_job")

        # test with multiple of the same job
        executionParamsList = [
            {"selector": selector, "mode": "default"},
            {"selector": selector, "mode": "default"},
            {"selector": selector, "mode": "default"},
        ]

        result = execute_dagster_graphql(
            context=graphql_context,
            query=LAUNCH_MULTIPLE_RUNS_MUTATION,
            variables={"executionParamsList": executionParamsList},
        )

        assert "launchMultipleRuns" in result.data
        launches = result.data["launchMultipleRuns"]
        assert launches["__typename"] == "LaunchMultipleRunsSuccess"

        run_ids = []
        runs = launches.get("runs", [])

        for run in runs:
            assert run["__typename"] == "LaunchRunSuccess"
            run_ids.append(run["run"]["runId"])

        wait_for_runs_to_finish(graphql_context.instance)

        for run_id in run_ids:
            result = execute_dagster_graphql(
                context=graphql_context, query=RUN_QUERY, variables={"runId": run_id}
            )
            assert result.data["pipelineRunOrError"]["__typename"] == "Run"
            assert result.data["pipelineRunOrError"]["status"] == "SUCCESS"

    def test_multiple_run_launcher_multiple_jobs(self, graphql_context: WorkspaceRequestContext):
        selectors = [
            infer_job_selector(graphql_context, "no_config_job"),
            infer_job_selector(graphql_context, "more_complicated_config", ["noop_op"]),
        ]

        # test with multiple of the same job
        executionParamsList = [
            {"selector": selectors[0], "mode": "default"},
            {"selector": selectors[1], "mode": "default"},
            {"selector": selectors[0], "mode": "default"},
            {"selector": selectors[1], "mode": "default"},
        ]

        result = execute_dagster_graphql(
            context=graphql_context,
            query=LAUNCH_MULTIPLE_RUNS_MUTATION,
            variables={"executionParamsList": executionParamsList},
        )

        assert "launchMultipleRuns" in result.data
        launches = result.data["launchMultipleRuns"]
        assert launches["__typename"] == "LaunchMultipleRunsSuccess"

        run_ids = []
        runs = launches.get("runs", [])

        for run in runs:
            assert run["__typename"] == "LaunchRunSuccess"
            run_ids.append(run["run"]["runId"])

        wait_for_runs_to_finish(graphql_context.instance)

        for run_id in run_ids:
            result = execute_dagster_graphql(
                context=graphql_context, query=RUN_QUERY, variables={"runId": run_id}
            )
            assert result.data["pipelineRunOrError"]["__typename"] == "Run"
            assert result.data["pipelineRunOrError"]["status"] == "SUCCESS"
            if result.data["pipelineRunOrError"].get("stats"):
                assert result.data["pipelineRunOrError"]["stats"]["stepsSucceeded"] == 1

    def test_multiple_launch_failure_unauthorized(self, graphql_context: WorkspaceRequestContext):
        executionParamsList = [
            {"selector": infer_job_selector(graphql_context, "no_config_job"), "mode": "default"},
            {"selector": infer_job_selector(graphql_context, "no_config_job"), "mode": "default"},
        ]

        # Mock `has_permission_for_location` to return False
        with patch.object(graphql_context, "has_permission_for_location", return_value=False):
            result = execute_dagster_graphql(
                context=graphql_context,
                query=LAUNCH_MULTIPLE_RUNS_MUTATION,
                variables={"executionParamsList": executionParamsList},
            )
            assert "launchMultipleRuns" in result.data
            unauthorized_error = result.data["launchMultipleRuns"]

            assert unauthorized_error["__typename"] == "PythonError"
            assert "message" in unauthorized_error
            assert "GrapheneUnauthorizedError" in unauthorized_error["message"]


class TestFailedLaunch(LaunchFailTestSuite):
    def test_launch_failure(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "no_config_job")
        result = execute_dagster_graphql(
            context=graphql_context,
            query=LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={"executionParams": {"selector": selector, "mode": "default"}},
        )
        assert result.data["launchPipelineExecution"]["__typename"] != "LaunchRunSuccess"

        # fetch the most recent run, which should be this one that just failed to launch
        run = graphql_context.instance.get_runs(limit=1)[0]

        result = execute_dagster_graphql(
            context=graphql_context, query=RUN_QUERY, variables={"runId": run.run_id}
        )
        assert result.data["pipelineRunOrError"]["__typename"] == "Run"
        assert result.data["pipelineRunOrError"]["status"] == "FAILURE"
        assert result.data["pipelineRunOrError"]["startTime"]
        assert result.data["pipelineRunOrError"]["endTime"]


class TestFailedMultipleLaunch(LaunchFailTestSuite):
    def test_multiple_launch_failure(self, graphql_context: WorkspaceRequestContext):
        executionParamsList = [
            {"selector": infer_job_selector(graphql_context, "no_config_job"), "mode": "default"},
            {"selector": infer_job_selector(graphql_context, "no_config_job"), "mode": "default"},
        ]

        result = execute_dagster_graphql(
            context=graphql_context,
            query=LAUNCH_MULTIPLE_RUNS_MUTATION,
            variables={"executionParamsList": executionParamsList},
        )

        assert result.data["launchMultipleRuns"]["__typename"] != "LaunchRunSuccess"

        # fetch the most recent runs
        run_ids = [run.run_id for run in graphql_context.instance.get_runs(limit=2)]

        for run_id in run_ids:
            result = execute_dagster_graphql(
                context=graphql_context, query=RUN_QUERY, variables={"runId": run_id}
            )
            assert result.data["pipelineRunOrError"]["__typename"] == "Run"
            assert result.data["pipelineRunOrError"]["status"] == "FAILURE"
            assert result.data["pipelineRunOrError"]["startTime"]
            assert result.data["pipelineRunOrError"]["endTime"]


class TestFailedMultipleLaunchReadOnly(ReadOnlyTestSuite):
    def test_multiple_launch_failure_readonly(self, graphql_context: WorkspaceRequestContext):
        executionParamsList = [
            {"selector": infer_job_selector(graphql_context, "no_config_job"), "mode": "default"},
            {"selector": infer_job_selector(graphql_context, "no_config_job"), "mode": "default"},
        ]

        result = execute_dagster_graphql(
            context=graphql_context,
            query=LAUNCH_MULTIPLE_RUNS_MUTATION,
            variables={"executionParamsList": executionParamsList},
        )

        assert result.data["launchMultipleRuns"]["__typename"] != "LaunchMultipleRunsSuccess"
        assert result.data["launchMultipleRuns"]["__typename"] == "PythonError"
        assert "message" in result.data["launchMultipleRuns"]
        assert "GrapheneUnauthorizedError" in result.data["launchMultipleRuns"]["message"]
