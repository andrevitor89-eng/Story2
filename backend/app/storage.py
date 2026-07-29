from __future__ import annotations

import io
from functools import lru_cache
from pathlib import Path

import boto3
from botocore.client import Config

from app.config import settings


def _local_root() -> Path:
    root = Path(settings.storage_local_path)
    root.mkdir(parents=True, exist_ok=True)
    return root


@lru_cache
def _client(endpoint: str):
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=settings.storage_access_key,
        aws_secret_access_key=settings.storage_secret_key,
        region_name=settings.storage_region,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def put_bytes(key: str, data: bytes, mime_type: str) -> str:
    if settings.storage_backend == "local":
        path = _local_root() / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    _client(settings.storage_endpoint_url).put_object(
        Bucket=settings.storage_bucket,
        Key=key,
        Body=data,
        ContentType=mime_type,
    )
    return key


def get_bytes(key: str) -> bytes:
    if settings.storage_backend == "local":
        path = _local_root() / key
        return path.read_bytes()

    obj = _client(settings.storage_endpoint_url).get_object(
        Bucket=settings.storage_bucket, Key=key
    )
    return obj["Body"].read()


def presigned_url(key: str, expires: int = 3600 * 24) -> str:
    """Assina com o host publico (ex.: localhost:9100) para o navegador validar SigV4."""
    if settings.storage_backend == "local":
        return key
    return _client(settings.storage_public_endpoint_url).generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.storage_bucket, "Key": key},
        ExpiresIn=expires,
    )


def put_fileobj(key: str, fileobj: io.BytesIO, mime_type: str) -> str:
    return put_bytes(key, fileobj.getvalue(), mime_type)
