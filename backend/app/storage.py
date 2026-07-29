from __future__ import annotations

import io
from functools import lru_cache
from pathlib import Path

import boto3
from botocore.client import Config

from app.config import settings
from app.db import SessionLocal
from app.models import StorageObject


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


def _db_put(key: str, data: bytes, mime_type: str) -> None:
    db = SessionLocal()
    try:
        obj = db.get(StorageObject, key)
        if obj is None:
            db.add(StorageObject(key=key, data=data, mime_type=mime_type))
        else:
            obj.data = data
            obj.mime_type = mime_type
        db.commit()
    finally:
        db.close()


def _db_get(key: str) -> bytes:
    db = SessionLocal()
    try:
        obj = db.get(StorageObject, key)
        if obj is None:
            raise FileNotFoundError(f"Storage key nao encontrado: {key}")
        return bytes(obj.data)
    finally:
        db.close()


def put_bytes(key: str, data: bytes, mime_type: str) -> str:
    backend = (settings.storage_backend or "local").lower()
    if backend == "db":
        _db_put(key, data, mime_type)
        return key

    if backend == "local":
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
    backend = (settings.storage_backend or "local").lower()
    if backend == "db":
        return _db_get(key)

    if backend == "local":
        path = _local_root() / key
        return path.read_bytes()

    obj = _client(settings.storage_endpoint_url).get_object(
        Bucket=settings.storage_bucket, Key=key
    )
    return obj["Body"].read()


def presigned_url(key: str, expires: int = 3600 * 24) -> str:
    """Assina com o host publico (ex.: localhost:9100) para o navegador validar SigV4."""
    backend = (settings.storage_backend or "local").lower()
    if backend in ("local", "db"):
        return key
    return _client(settings.storage_public_endpoint_url).generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.storage_bucket, "Key": key},
        ExpiresIn=expires,
    )


def put_fileobj(key: str, fileobj: io.BytesIO, mime_type: str) -> str:
    return put_bytes(key, fileobj.getvalue(), mime_type)
