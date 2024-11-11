import subprocess
from typing import Generator

import pytest
import requests
from airlift_federation_tutorial_tests.conftest import ORIG_DEFS_FILE, makefile_dir, replace_file
from dagster_airlift.in_airflow.gql_queries import VERIFICATION_QUERY
from dagster_airlift.test.shared_fixtures import stand_up_dagster

STAGE_FILE = ORIG_DEFS_FILE.parent / "stages" / "with_specs.py"


@pytest.fixture
def completed_stage() -> Generator[None, None, None]:
    with replace_file(ORIG_DEFS_FILE, STAGE_FILE):
        yield


@pytest.fixture(name="dagster_dev")
def dagster_fixture(
    upstream_airflow: subprocess.Popen, downstream_airflow: subprocess.Popen, completed_stage: None
) -> Generator[subprocess.Popen, None, None]:
    process = None
    try:
        with stand_up_dagster(
            dagster_dev_cmd=["make", "-C", str(makefile_dir()), "dagster_run"],
            port=3000,
        ) as process:
            yield process
    finally:
        if process:
            process.terminate()


def test_with_specs(dagster_dev: subprocess.Popen) -> None:
    response = requests.post(
        # Timeout in seconds
        "http://localhost:3000/graphql",
        json={"query": VERIFICATION_QUERY},
        timeout=3,
    )
    assert response.status_code == 200
