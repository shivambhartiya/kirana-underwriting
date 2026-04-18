from urllib.parse import urljoin

import boto3

from app.core.config import get_settings


settings = get_settings()


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
    )


def ensure_bucket() -> None:
    client = get_s3_client()
    existing = [bucket["Name"] for bucket in client.list_buckets().get("Buckets", [])]
    if settings.s3_bucket not in existing:
        client.create_bucket(Bucket=settings.s3_bucket)


def create_presigned_upload(object_key: str, content_type: str) -> str:
    try:
        client = get_s3_client()
        presigned = client.generate_presigned_url(
            "put_object",
            Params={"Bucket": settings.s3_bucket, "Key": object_key, "ContentType": content_type},
            ExpiresIn=settings.upload_url_ttl_seconds,
        )
        if settings.s3_public_endpoint and settings.s3_public_endpoint != settings.s3_endpoint:
            return presigned.replace(settings.s3_endpoint, settings.s3_public_endpoint)
        return presigned
    except Exception:
        endpoint = settings.s3_public_endpoint or settings.s3_endpoint
        return urljoin(f"{endpoint}/", f"{settings.s3_bucket}/{object_key}")
