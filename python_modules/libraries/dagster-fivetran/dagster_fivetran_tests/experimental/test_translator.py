from typing import Callable

from dagster_fivetran import FivetranWorkspace


def test_fivetran_workspace_data_to_fivetran_connector_table_props_data(
    account_id: str,
    api_key: str,
    api_secret: str,
    fetch_workspace_data_api_mocks: Callable,
) -> None:
    resource = FivetranWorkspace(account_id=account_id, api_key=api_key, api_secret=api_secret)

    actual_workspace_data = resource.fetch_fivetran_workspace_data()
    table_props_data = actual_workspace_data.to_fivetran_connector_table_props_data()
    assert len(table_props_data) == 4
    assert table_props_data[0].table == "schema_name_in_destination_1.table_name_in_destination_1"
    assert table_props_data[1].table == "schema_name_in_destination_1.table_name_in_destination_2"
    assert table_props_data[2].table == "schema_name_in_destination_2.table_name_in_destination_1"
    assert table_props_data[3].table == "schema_name_in_destination_2.table_name_in_destination_2"
