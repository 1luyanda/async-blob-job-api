from app.config import Settings
from app.storage import resolve_target


def test_resolve_target_uses_shared_settings():
    settings = Settings(
        azure_storage_connection_string="shared-conn",
        azure_storage_container="jobs",
    )
    json_conn, json_container, json_folder = resolve_target("json", settings)
    parquet_conn, parquet_container, parquet_folder = resolve_target("parquet", settings)
    assert json_folder == "json"
    assert parquet_folder == "parquet"
    assert json_conn == parquet_conn == "shared-conn"
    assert json_container == parquet_container == "jobs"


def test_resolve_target_prefers_dedicated_accounts():
    settings = Settings(
        azure_storage_connection_string="shared-conn",
        azure_storage_container="jobs",
        azure_json_storage_connection_string="json-conn",
        azure_json_storage_container="json-container",
        azure_parquet_storage_connection_string="parquet-conn",
        azure_parquet_storage_container="parquet-container",
    )
    json_conn, json_container, json_folder = resolve_target("json", settings)
    parquet_conn, parquet_container, parquet_folder = resolve_target("parquet", settings)
    assert (json_conn, json_container, json_folder) == ("json-conn", "json-container", "json")
    assert (parquet_conn, parquet_container, parquet_folder) == (
        "parquet-conn",
        "parquet-container",
        "parquet",
    )
