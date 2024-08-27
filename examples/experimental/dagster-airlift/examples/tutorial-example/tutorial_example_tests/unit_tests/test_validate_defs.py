# For some reason the buildkite job is not finding the manifest.json
# from pathlib import Path
#
# from dagster import AssetSpec, Definitions, multi_asset
# from dagster_airlift.core import dag_defs, task_defs
# from dagster_airlift.dbt.multi_asset import dbt_defs
# from dagster_dbt import DbtProject
# from tutorial_example.dagster_defs.build_dag_defs import build_dag_defs
#
#
# def dbt_project_path() -> Path:
#     return Path(__file__).parent / "dbt"
#
#
# def duckdb_path() -> Path:
#     return Path(__file__).parent / "jaffle_shop.duckdb"
#
#
# def test_loadable():
#     dag_defs = build_dag_defs(
#         duckdb_path=duckdb_path(),
#         dbt_project_path=dbt_project_path(),
#     )
#     Definitions.validate_loadable(dag_defs)
#
#
# def test_dbt_defs():
#     defs = dbt_defs(
#         manifest=dbt_project_path() / "target" / "manifest.json",
#         project=DbtProject(dbt_project_path()),
#     )
#
#     Definitions.validate_loadable(defs)
#
#
# def test_dbt_defs_in_task_defs():
#     defs = dag_defs(
#         task_defs(
#             "build_dbt_models",
#             dbt_defs(
#                 manifest=dbt_project_path() / "target" / "manifest.json",
#                 project=DbtProject(dbt_project_path()),
#             ),
#         )
#     )
#
#     Definitions.validate_loadable(defs)
#
#
# def test_dbt_defs_collision_minimal_repro() -> None:
#     @multi_asset(specs=[AssetSpec(key="some_key")])
#     def an_asset(): ...
#
#     defs = dag_defs(
#         "some_dag",
#         task_defs(
#             "t1",
#             dbt_defs(
#                 manifest=dbt_project_path() / "target" / "manifest.json",
#                 project=DbtProject(dbt_project_path()),
#             ),
#         ),
#         task_defs(
#             "t2",
#             Definitions(assets=[an_asset]),
#         ),
#     )
#
#     Definitions.validate_loadable(defs)
#