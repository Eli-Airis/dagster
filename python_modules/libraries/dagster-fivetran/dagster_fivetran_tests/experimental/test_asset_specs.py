import responses
from dagster._config.field_utils import EnvVar
from dagster._core.test_utils import environ
from dagster_fivetran import FivetranWorkspace, load_fivetran_asset_specs


def test_fetch_fivetran_workspace_data(
    account_id: str,
    api_key: str,
    api_secret: str,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    resource = FivetranWorkspace(account_id=account_id, api_key=api_key, api_secret=api_secret)

    actual_workspace_data = resource.fetch_fivetran_workspace_data()
    assert len(actual_workspace_data.connectors_by_id) == 1
    assert len(actual_workspace_data.destinations_by_id) == 1


def test_translator_spec(fetch_workspace_data_api_mocks: responses.RequestsMock) -> None:
    account_id = "fake_account_id"
    api_key = uuid.uuid4().hex
    api_secret = uuid.uuid4().hex

    with environ({"FIVETRAN_API_KEY": api_key, "FIVETRAN_API_SECRET": api_secret}):
        resource = FivetranWorkspace(
            account_id=account_id,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        all_assets = load_fivetran_asset_specs(resource)
        all_assets_keys = [asset.key for asset in all_assets]

        # 4 tables for the connector
        assert len(all_assets) == 4
        assert len(all_assets_keys) == 4

        # Sanity check outputs, translator tests cover details here
        first_asset_key = next(key for key in all_assets_keys)
        assert first_asset_key.path == [
            "schema_name_in_destination_1",
            "table_name_in_destination_1",
        ]
