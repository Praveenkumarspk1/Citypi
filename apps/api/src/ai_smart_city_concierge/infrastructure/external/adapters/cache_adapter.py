"""
Cache Service Adapters
"""
from abc import ABC, abstractmethod
from typing import Any

from ....application.ports.external_services import CacheServicePort


class BaseCacheAdapter(CacheServicePort, ABC):
    """Base cache adapter"""

    @abstractmethod
    async def _get_request(self, key: str) -> Any | None:
        """Get value request"""
        pass

    @abstractmethod
    async def _set_request(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None,
    ) -> None:
        """Set value request"""
        pass

    @abstractmethod
    async def _delete_request(self, key: str) -> None:
        """Delete value request"""
        pass

    @abstractmethod
    async def _exists_request(self, key: str) -> bool:
        """Exists request"""
        pass

    @abstractmethod
    async def _increment_request(self, key: str, amount: int) -> int:
        """Increment request"""
        pass

    @abstractmethod
    async def _get_multi_request(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values request"""
        pass

    @abstractmethod
    async def _set_multi_request(
        self,
        mapping: dict[str, Any],
        ttl_seconds: int | None,
    ) -> None:
        """Set multiple values request"""
        pass

    async def get(self, key: str) -> Any | None:
        """Get value from cache"""
        return await self._get_request(key)

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> None:
        """Set value in cache"""
        await self._set_request(key, value, ttl_seconds)

    async def delete(self, key: str) -> None:
        """Delete value from cache"""
        await self._delete_request(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        return await self._exists_request(key)

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        return await self._increment_request(key, amount)

    async def get_multi(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values"""
        return await self._get_multi_request(keys)

    async def set_multi(
        self,
        mapping: dict[str, Any],
        ttl_seconds: int | None = None,
    ) -> None:
        """Set multiple values"""
        await self._set_multi_request(mapping, ttl_seconds)


class RedisCacheAdapter(BaseCacheAdapter):
    """Redis cache adapter"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        ssl: bool = False,
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.ssl = ssl
        self._client = None

    async def _get_client(self):
        if self._client is None:
            import redis.asyncio as redis
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                ssl=self.ssl,
                decode_responses=True,
            )
        return self._client

    async def _get_request(self, key: str) -> Any | None:
        client = await self._get_client()
        value = await client.get(key)
        if value is not None:
            import json
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def _set_request(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None,
    ) -> None:
        client = await self._get_client()
        import json
        serialized = json.dumps(value, default=str)
        if ttl_seconds:
            await client.setex(key, ttl_seconds, serialized)
        else:
            await client.set(key, serialized)

    async def _delete_request(self, key: str) -> None:
        client = await self._get_client()
        await client.delete(key)

    async def _exists_request(self, key: str) -> bool:
        client = await self._get_client()
        return await client.exists(key) > 0

    async def _increment_request(self, key: str, amount: int) -> int:
        client = await self._get_client()
        return await client.incrby(key, amount)

    async def _get_multi_request(self, keys: list[str]) -> dict[str, Any]:
        client = await self._get_client()
        values = await client.mget(keys)
        import json
        result = {}
        for key, value in zip(keys, values, strict=False):
            if value is not None:
                try:
                    result[key] = json.loads(value)
                except json.JSONDecodeError:
                    result[key] = value
        return result

    async def _set_multi_request(
        self,
        mapping: dict[str, Any],
        ttl_seconds: int | None,
    ) -> None:
        client = await self._get_client()
        import json
        pipe = client.pipeline()
        for key, value in mapping.items():
            serialized = json.dumps(value, default=str)
            if ttl_seconds:
                pipe.setex(key, ttl_seconds, serialized)
            else:
                pipe.set(key, serialized)
        await pipe.execute()

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None


class MemcachedCacheAdapter(BaseCacheAdapter):
    """Memcached cache adapter"""

    def __init__(self, servers: list[str] = None):
        self.servers = servers or ["localhost:11211"]
        self._client = None

    async def _get_client(self):
        if self._client is None:
            import aiomcache
            # Parse servers
            host, port = self.servers[0].split(":")
            self._client = aiomcache.Client(host, int(port))
        return self._client

    async def _get_request(self, key: str) -> Any | None:
        client = await self._get_client()
        value = await client.get(key.encode())
        if value is not None:
            import json
            try:
                return json.loads(value.decode())
            except json.JSONDecodeError:
                return value.decode()
        return None

    async def _set_request(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None,
    ) -> None:
        client = await self._get_client()
        import json
        serialized = json.dumps(value, default=str).encode()
        if ttl_seconds:
            await client.set(key.encode(), serialized, exptime=ttl_seconds)
        else:
            await client.set(key.encode(), serialized)

    async def _delete_request(self, key: str) -> None:
        client = await self._get_client()
        await client.delete(key.encode())

    async def _exists_request(self, key: str) -> bool:
        # Memcached doesn't have exists, use get
        value = await self._get_request(key)
        return value is not None

    async def _increment_request(self, key: str, amount: int) -> int:
        client = await self._get_client()
        # Memcached increment returns new value
        return await client.increment(key.encode(), amount)

    async def _get_multi_request(self, keys: list[str]) -> dict[str, Any]:
        await self._get_client()
        # aiomcache doesn't have mget, do individual gets
        result = {}
        for key in keys:
            value = await self._get_request(key)
            if value is not None:
                result[key] = value
        return result

    async def _set_multi_request(
        self,
        mapping: dict[str, Any],
        ttl_seconds: int | None,
    ) -> None:
        for key, value in mapping.items():
            await self._set_request(key, value, ttl_seconds)

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None


class InMemoryCacheAdapter(BaseCacheAdapter):
    """In-memory cache adapter (for development/testing)"""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._cache: dict[str, Any] = {}
        self._ttl: dict[str, float] = {}
        self._access_times: dict[str, float] = {}

    async def _get_request(self, key: str) -> Any | None:
        import time
        # Check TTL
        if key in self._ttl:
            if time.time() > self._ttl[key]:
                # Expired
                del self._cache[key]
                del self._ttl[key]
                if key in self._access_times:
                    del self._access_times[key]
                return None

        self._access_times[key] = time.time()
        return self._cache.get(key)

    async def _set_request(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None,
    ) -> None:
        import time

        # Evict if at max size
        if len(self._cache) >= self.max_size and key not in self._cache:
            # Remove least recently used
            lru_key = min(self._access_times, key=self._access_times.get)
            del self._cache[lru_key]
            if lru_key in self._ttl:
                del self._ttl[lru_key]
            del self._access_times[lru_key]

        self._cache[key] = value
        self._access_times[key] = time.time()

        if ttl_seconds:
            self._ttl[key] = time.time() + ttl_seconds
        elif key in self._ttl:
            del self._ttl[key]

    async def _delete_request(self, key: str) -> None:
        self._cache.pop(key, None)
        self._ttl.pop(key, None)
        self._access_times.pop(key, None)

    async def _exists_request(self, key: str) -> bool:
        return await self._get_request(key) is not None

    async def _increment_request(self, key: str, amount: int) -> int:
        current = await self._get_request(key) or 0
        try:
            new_value = int(current) + amount
        except (ValueError, TypeError):
            new_value = amount
        await self._set_request(key, new_value, None)
        return new_value

    async def _get_multi_request(self, keys: list[str]) -> dict[str, Any]:
        result = {}
        for key in keys:
            value = await self._get_request(key)
            if value is not None:
                result[key] = value
        return result

    async def _set_multi_request(
        self,
        mapping: dict[str, Any],
        ttl_seconds: int | None,
    ) -> None:
        for key, value in mapping.items():
            await self._set_request(key, value, ttl_seconds)

    async def clear(self):
        """Clear all cache"""
        self._cache.clear()
        self._ttl.clear()
        self._access_times.clear()
