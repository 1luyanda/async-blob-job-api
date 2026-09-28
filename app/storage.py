from azure.core.exceptions import HttpResponseError, ResourceExistsError
from azure.storage.blob import BlobServiceClient, ContentSettings

from app.config import Settings, get_settings


class AzureStorageError(RuntimeError):
    """Raised when Azure Blob Storage is not configured or an upload fails."""


def _shared_or(specific_value: str, shared_value: str) -> str:
    return specific_value.strip() or shared_value.strip()


def resolve_target(kind: str, settings: Settings | None = None) -> tuple[str, str, str]:
    """Return (connection_string, container, folder) for json or parquet."""
    settings = settings or get_settings()
    if kind == "json":
        connection = _shared_or(
            settings.azure_json_storage_connection_string,
            settings.azure_storage_connection_string,
        )
        container = _shared_or(
            settings.azure_json_storage_container,
            settings.azure_storage_container,
        )
        folder = "json"
    elif kind == "parquet":
        connection = _shared_or(
            settings.azure_parquet_storage_connection_string,
            settings.azure_storage_connection_string,
        )
        container = _shared_or(
            settings.azure_parquet_storage_container,
            settings.azure_storage_container,
        )
        folder = "parquet"
    else:
        raise AzureStorageError(f"Unknown output kind: {kind}")

    if not connection:
        raise AzureStorageError(
            f"No Azure connection string for {kind}. Set AZURE_STORAGE_CONNECTION_STRING "
            f"or AZURE_{kind.upper()}_STORAGE_CONNECTION_STRING in .env."
        )
    if not container:
        raise AzureStorageError(
            f"No Azure container for {kind}. Set AZURE_STORAGE_CONTAINER "
            f"or AZURE_{kind.upper()}_STORAGE_CONTAINER in .env."
        )
    return connection, container, folder


def _client(connection_string: str) -> BlobServiceClient:
    return BlobServiceClient.from_connection_string(connection_string)


def ensure_container(connection_string: str, container: str) -> None:
    service = _client(connection_string)
    try:
        service.create_container(container)
    except ResourceExistsError:
        return
    except HttpResponseError as exc:
        if exc.status_code == 409:
            return
        raise


def upload_blob(
    data: bytes,
    blob_path: str,
    content_type: str,
    connection_string: str,
    container: str,
) -> tuple[str, str]:
    """Upload bytes and return (blob_path, blob_url)."""
    ensure_container(connection_string, container)
    blob = _client(connection_string).get_blob_client(container=container, blob=blob_path)
    blob.upload_blob(
        data,
        overwrite=True,
        content_settings=ContentSettings(content_type=content_type),
    )
    return blob_path, blob.url


def upload_job_outputs(job_id: str, json_bytes: bytes, parquet_bytes: bytes) -> dict[str, str]:
    json_conn, json_container, json_folder = resolve_target("json")
    parquet_conn, parquet_container, parquet_folder = resolve_target("parquet")

    json_path, json_url = upload_blob(
        json_bytes,
        f"{json_folder}/{job_id}.json",
        "application/json",
        json_conn,
        json_container,
    )
    parquet_path, parquet_url = upload_blob(
        parquet_bytes,
        f"{parquet_folder}/{job_id}.parquet",
        "application/octet-stream",
        parquet_conn,
        parquet_container,
    )
    return {
        "json_blob_path": json_path,
        "json_blob_url": json_url,
        "parquet_blob_path": parquet_path,
        "parquet_blob_url": parquet_url,
    }
