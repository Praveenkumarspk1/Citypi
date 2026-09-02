"""
Storage Service Adapters
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ....application.ports.external_services import StorageServicePort


@dataclass
class StorageObject:
    """Storage object metadata"""
    key: str
    size: int
    content_type: str
    last_modified: str
    etag: str
    metadata: dict[str, str]


class BaseStorageAdapter(StorageServicePort, ABC):
    """Base storage adapter"""

    @abstractmethod
    async def _upload_request(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str,
        metadata: dict[str, str] | None,
    ) -> str:
        """Upload file request"""
        pass

    @abstractmethod
    async def _download_request(self, bucket: str, key: str) -> bytes:
        """Download file request"""
        pass

    @abstractmethod
    async def _delete_request(self, bucket: str, key: str) -> None:
        """Delete file request"""
        pass

    @abstractmethod
    async def _generate_presigned_url_request(
        self,
        bucket: str,
        key: str,
        expiration_seconds: int,
    ) -> str:
        """Generate presigned URL request"""
        pass

    @abstractmethod
    async def _list_objects_request(
        self,
        bucket: str,
        prefix: str,
        max_keys: int,
    ) -> list[StorageObject]:
        """List objects request"""
        pass

    async def upload(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Upload file"""
        return await self._upload_request(bucket, key, data, content_type, metadata)

    async def download(self, bucket: str, key: str) -> bytes:
        """Download file"""
        return await self._download_request(bucket, key)

    async def delete(self, bucket: str, key: str) -> None:
        """Delete file"""
        await self._delete_request(bucket, key)

    async def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        expiration_seconds: int = 3600,
    ) -> str:
        """Generate presigned URL"""
        return await self._generate_presigned_url_request(bucket, key, expiration_seconds)

    async def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> list[dict[str, Any]]:
        """List objects in bucket"""
        objects = await self._list_objects_request(bucket, prefix, max_keys)
        return [
            {
                "key": obj.key,
                "size": obj.size,
                "content_type": obj.content_type,
                "last_modified": obj.last_modified,
                "etag": obj.etag,
                "metadata": obj.metadata,
            }
            for obj in objects
        ]


class S3StorageAdapter(BaseStorageAdapter):
    """AWS S3 storage adapter"""

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        region: str = "us-east-1",
        endpoint_url: str | None = None,
    ):
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.endpoint_url = endpoint_url
        self._client = None

    async def _get_client(self):
        if self._client is None:
            import aioboto3
            session = aioboto3.Session(
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
            )
            self._client = session.client(
                "s3",
                endpoint_url=self.endpoint_url,
            )
        return self._client

    async def _upload_request(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str,
        metadata: dict[str, str] | None,
    ) -> str:
        client = await self._get_client()

        extra_args = {"ContentType": content_type}
        if metadata:
            extra_args["Metadata"] = metadata

        await client.put_object(
            Bucket=bucket,
            Key=key,
            Body=data,
            **extra_args,
        )

        return f"s3://{bucket}/{key}"

    async def _download_request(self, bucket: str, key: str) -> bytes:
        client = await self._get_client()

        response = await client.get_object(Bucket=bucket, Key=key)
        return await response["Body"].read()

    async def _delete_request(self, bucket: str, key: str) -> None:
        client = await self._get_client()
        await client.delete_object(Bucket=bucket, Key=key)

    async def _generate_presigned_url_request(
        self,
        bucket: str,
        key: str,
        expiration_seconds: int,
    ) -> str:
        client = await self._get_client()

        url = await client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expiration_seconds,
        )

        return url

    async def _list_objects_request(
        self,
        bucket: str,
        prefix: str,
        max_keys: int,
    ) -> list[StorageObject]:
        client = await self._get_client()

        response = await client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix,
            MaxKeys=max_keys,
        )

        objects = []
        for obj in response.get("Contents", []):
            objects.append(StorageObject(
                key=obj["Key"],
                size=obj["Size"],
                content_type="",  # Would need HEAD request
                last_modified=obj["LastModified"].isoformat(),
                etag=obj["ETag"].strip('"'),
                metadata={},
            ))

        return objects

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None


class GCSStorageAdapter(BaseStorageAdapter):
    """Google Cloud Storage adapter"""

    def __init__(self, credentials_path: str | None = None, project: str | None = None):
        self.credentials_path = credentials_path
        self.project = project
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from google.cloud import storage
            if self.credentials_path:
                self._client = storage.Client.from_service_account_json(
                    self.credentials_path,
                    project=self.project,
                )
            else:
                self._client = storage.Client(project=self.project)
        return self._client

    async def _upload_request(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str,
        metadata: dict[str, str] | None,
    ) -> str:
        client = await self._get_client()

        bucket_obj = client.bucket(bucket)
        blob = bucket_obj.blob(key)
        blob.content_type = content_type

        if metadata:
            blob.metadata = metadata

        blob.upload_from_string(data)

        return f"gs://{bucket}/{key}"

    async def _download_request(self, bucket: str, key: str) -> bytes:
        client = await self._get_client()

        bucket_obj = client.bucket(bucket)
        blob = bucket_obj.blob(key)
        return blob.download_as_bytes()

    async def _delete_request(self, bucket: str, key: str) -> None:
        client = await self._get_client()

        bucket_obj = client.bucket(bucket)
        blob = bucket_obj.blob(key)
        blob.delete()

    async def _generate_presigned_url_request(
        self,
        bucket: str,
        key: str,
        expiration_seconds: int,
    ) -> str:
        client = await self._get_client()

        bucket_obj = client.bucket(bucket)
        blob = bucket_obj.blob(key)

        url = blob.generate_signed_url(
            expiration=expiration_seconds,
            method="GET",
        )

        return url

    async def _list_objects_request(
        self,
        bucket: str,
        prefix: str,
        max_keys: int,
    ) -> list[StorageObject]:
        client = await self._get_client()

        bucket_obj = client.bucket(bucket)
        blobs = bucket_obj.list_blobs(prefix=prefix, max_results=max_keys)

        objects = []
        for blob in blobs:
            objects.append(StorageObject(
                key=blob.name,
                size=blob.size,
                content_type=blob.content_type or "",
                last_modified=blob.updated.isoformat() if blob.updated else "",
                etag=blob.etag or "",
                metadata=blob.metadata or {},
            ))

        return objects


class AzureBlobStorageAdapter(BaseStorageAdapter):
    """Azure Blob Storage adapter"""

    def __init__(
        self,
        account_name: str,
        account_key: str,
        container_name: str = "default",
    ):
        self.account_name = account_name
        self.account_key = account_key
        self.container_name = container_name
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from azure.storage.blob.aio import BlobServiceClient
            self._client = BlobServiceClient(
                account_url=f"https://{self.account_name}.blob.core.windows.net",
                credential=self.account_key,
            )
        return self._client

    async def _upload_request(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str,
        metadata: dict[str, str] | None,
    ) -> str:
        client = await self._get_client()

        container_client = client.get_container_client(bucket)
        blob_client = container_client.get_blob_client(key)

        await blob_client.upload_blob(
            data,
            content_type=content_type,
            metadata=metadata,
            overwrite=True,
        )

        return f"https://{self.account_name}.blob.core.windows.net/{bucket}/{key}"

    async def _download_request(self, bucket: str, key: str) -> bytes:
        client = await self._get_client()

        container_client = client.get_container_client(bucket)
        blob_client = container_client.get_blob_client(key)

        stream = await blob_client.download_blob()
        return await stream.readall()

    async def _delete_request(self, bucket: str, key: str) -> None:
        client = await self._get_client()

        container_client = client.get_container_client(bucket)
        blob_client = container_client.get_blob_client(key)
        await blob_client.delete_blob()

    async def _generate_presigned_url_request(
        self,
        bucket: str,
        key: str,
        expiration_seconds: int,
    ) -> str:
        await self._get_client()

        from datetime import datetime, timedelta

        from azure.storage.blob import BlobSasPermissions, generate_blob_sas

        sas_token = generate_blob_sas(
            account_name=self.account_name,
            container_name=bucket,
            blob_name=key,
            account_key=self.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(seconds=expiration_seconds),
        )

        return f"https://{self.account_name}.blob.core.windows.net/{bucket}/{key}?{sas_token}"

    async def _list_objects_request(
        self,
        bucket: str,
        prefix: str,
        max_keys: int,
    ) -> list[StorageObject]:
        client = await self._get_client()

        container_client = client.get_container_client(bucket)
        blobs = container_client.list_blobs(name_starts_with=prefix, max_results=max_keys)

        objects = []
        async for blob in blobs:
            objects.append(StorageObject(
                key=blob.name,
                size=blob.size,
                content_type=blob.content_settings.content_type or "",
                last_modified=blob.last_modified.isoformat() if blob.last_modified else "",
                etag=blob.etag or "",
                metadata=blob.metadata or {},
            ))

        return objects

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None


class LocalStorageAdapter(BaseStorageAdapter):
    """Local filesystem storage adapter (for development/testing)"""

    def __init__(self, base_path: str = "./storage"):
        self.base_path = base_path
        import os
        os.makedirs(base_path, exist_ok=True)

    def _get_full_path(self, bucket: str, key: str) -> str:
        import os
        bucket_path = os.path.join(self.base_path, bucket)
        os.makedirs(bucket_path, exist_ok=True)
        return os.path.join(bucket_path, key)

    async def _upload_request(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str,
        metadata: dict[str, str] | None,
    ) -> str:
        import json

        full_path = self._get_full_path(bucket, key)

        with open(full_path, "wb") as f:
            f.write(data)

        # Store metadata separately
        if metadata:
            meta_path = full_path + ".meta"
            with open(meta_path, "w") as f:
                json.dump({
                    "content_type": content_type,
                    "metadata": metadata,
                }, f)

        return f"file://{full_path}"

    async def _download_request(self, bucket: str, key: str) -> bytes:
        full_path = self._get_full_path(bucket, key)

        with open(full_path, "rb") as f:
            return f.read()

    async def _delete_request(self, bucket: str, key: str) -> None:
        import os

        full_path = self._get_full_path(bucket, key)
        if os.path.exists(full_path):
            os.remove(full_path)

        meta_path = full_path + ".meta"
        if os.path.exists(meta_path):
            os.remove(meta_path)

    async def _generate_presigned_url_request(
        self,
        bucket: str,
        key: str,
        expiration_seconds: int,
    ) -> str:
        # Local files don't have presigned URLs
        return f"file://{self._get_full_path(bucket, key)}"

    async def _list_objects_request(
        self,
        bucket: str,
        prefix: str,
        max_keys: int,
    ) -> list[StorageObject]:
        import os
        from datetime import datetime

        bucket_path = os.path.join(self.base_path, bucket)
        if not os.path.exists(bucket_path):
            return []

        objects = []
        for root, _dirs, files in os.walk(bucket_path):
            for file in files:
                if file.endswith(".meta"):
                    continue

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, bucket_path)

                if prefix and not rel_path.startswith(prefix):
                    continue

                stat = os.stat(full_path)

                # Read metadata
                meta_path = full_path + ".meta"
                content_type = ""
                metadata = {}
                if os.path.exists(meta_path):
                    import json
                    with open(meta_path) as f:
                        meta = json.load(f)
                        content_type = meta.get("content_type", "")
                        metadata = meta.get("metadata", {})

                objects.append(StorageObject(
                    key=rel_path,
                    size=stat.st_size,
                    content_type=content_type,
                    last_modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    etag="",
                    metadata=metadata,
                ))

                if len(objects) >= max_keys:
                    break

        return objects
