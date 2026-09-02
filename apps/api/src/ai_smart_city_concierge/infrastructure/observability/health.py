"""
Health Checks
"""
import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class HealthStatus(StrEnum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Individual health check"""
    name: str
    status: HealthStatus = HealthStatus.UNKNOWN
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() + "Z",
            "duration_ms": self.duration_ms,
        }


@dataclass
class HealthCheckResult:
    """Overall health check result"""
    status: HealthStatus = HealthStatus.UNKNOWN
    checks: list[HealthCheck] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    service: str = "ai-smart-city-concierge"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "version": self.version,
            "service": self.service,
            "timestamp": self.timestamp.isoformat() + "Z",
            "checks": [check.to_dict() for check in self.checks],
        }

    @property
    def is_healthy(self) -> bool:
        return self.status == HealthStatus.HEALTHY

    @property
    def is_degraded(self) -> bool:
        return self.status == HealthStatus.DEGRADED


class HealthChecker:
    """Health check orchestrator"""

    def __init__(self, service_name: str = "ai-smart-city-concierge", version: str = "1.0.0"):
        self.service_name = service_name
        self.version = version
        self._checks: dict[str, Callable] = {}
        self._critical_checks: list[str] = []

    def register_check(
        self,
        name: str,
        check_func: Callable[[], Any],
        critical: bool = False,
        timeout: float = 5.0,
    ) -> None:
        """Register a health check"""
        async def wrapped_check() -> HealthCheck:
            start = datetime.utcnow()
            try:
                # Run with timeout
                result = await asyncio.wait_for(check_func(), timeout=timeout)
                duration = (datetime.utcnow() - start).total_seconds() * 1000

                if isinstance(result, HealthCheck):
                    result.duration_ms = duration
                    return result
                elif isinstance(result, bool):
                    return HealthCheck(
                        name=name,
                        status=HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY,
                        duration_ms=duration,
                    )
                elif isinstance(result, dict):
                    return HealthCheck(
                        name=name,
                        status=HealthStatus(result.get("status", "healthy")),
                        message=result.get("message", ""),
                        details=result.get("details", {}),
                        duration_ms=duration,
                    )
                else:
                    return HealthCheck(
                        name=name,
                        status=HealthStatus.HEALTHY,
                        message=str(result),
                        duration_ms=duration,
                    )
            except TimeoutError:
                duration = (datetime.utcnow() - start).total_seconds() * 1000
                return HealthCheck(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check timed out after {timeout}s",
                    duration_ms=duration,
                )
            except Exception as e:
                duration = (datetime.utcnow() - start).total_seconds() * 1000
                return HealthCheck(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(e)}",
                    duration_ms=duration,
                )

        self._checks[name] = wrapped_check
        if critical:
            self._critical_checks.append(name)

    def unregister_check(self, name: str) -> bool:
        """Unregister a health check"""
        if name in self._checks:
            del self._checks[name]
            if name in self._critical_checks:
                self._critical_checks.remove(name)
            return True
        return False

    async def run_checks(self, check_names: list[str] | None = None) -> HealthCheckResult:
        """Run all or specific health checks"""
        checks_to_run = check_names or list(self._checks.keys())

        # Run checks concurrently
        tasks = []
        for name in checks_to_run:
            if name in self._checks:
                tasks.append(self._checks[name]())

        results = await asyncio.gather(*tasks, return_exceptions=True)

        checks = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                checks.append(HealthCheck(
                    name=checks_to_run[i],
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check raised exception: {str(result)}",
                ))
            elif isinstance(result, HealthCheck):
                checks.append(result)
            else:
                checks.append(HealthCheck(
                    name=checks_to_run[i],
                    status=HealthStatus.UNKNOWN,
                    message=f"Unexpected result type: {type(result)}",
                ))

        # Determine overall status
        overall_status = self._determine_overall_status(checks)

        return HealthCheckResult(
            status=overall_status,
            checks=checks,
            version=self.version,
            service=self.service_name,
        )

    def _determine_overall_status(self, checks: list[HealthCheck]) -> HealthStatus:
        """Determine overall health status"""
        if not checks:
            return HealthStatus.UNKNOWN

        # Check critical checks first
        critical_failed = False
        for check in checks:
            if check.name in self._critical_checks:
                if check.status == HealthStatus.UNHEALTHY:
                    critical_failed = True
                    break

        if critical_failed:
            return HealthStatus.UNHEALTHY

        # Check for any unhealthy
        has_unhealthy = any(c.status == HealthStatus.UNHEALTHY for c in checks)
        has_degraded = any(c.status == HealthStatus.DEGRADED for c in checks)

        if has_unhealthy:
            return HealthStatus.UNHEALTHY
        elif has_degraded:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    async def run_single_check(self, name: str) -> HealthCheck:
        """Run a single health check"""
        if name not in self._checks:
            return HealthCheck(
                name=name,
                status=HealthStatus.UNKNOWN,
                message="Check not found",
            )

        return await self._checks[name]()


# Standard health checks
async def check_database(session_factory) -> HealthCheck:
    """Check database connectivity"""
    start = datetime.utcnow()
    try:
        async with session_factory() as session:
            await session.execute("SELECT 1")
        duration = (datetime.utcnow() - start).total_seconds() * 1000
        return HealthCheck(
            name="database",
            status=HealthStatus.HEALTHY,
            message="Database connection successful",
            duration_ms=duration,
        )
    except Exception as e:
        duration = (datetime.utcnow() - start).total_seconds() * 1000
        return HealthCheck(
            name="database",
            status=HealthStatus.UNHEALTHY,
            message=f"Database connection failed: {str(e)}",
            duration_ms=duration,
        )


async def check_redis(redis_client) -> HealthCheck:
    """Check Redis connectivity"""
    start = datetime.utcnow()
    try:
        await redis_client.ping()
        duration = (datetime.utcnow() - start).total_seconds() * 1000
        return HealthCheck(
            name="redis",
            status=HealthStatus.HEALTHY,
            message="Redis connection successful",
            duration_ms=duration,
        )
    except Exception as e:
        duration = (datetime.utcnow() - start).total_seconds() * 1000
        return HealthCheck(
            name="redis",
            status=HealthStatus.UNHEALTHY,
            message=f"Redis connection failed: {str(e)}",
            duration_ms=duration,
        )


async def check_vector_db(vector_store) -> HealthCheck:
    """Check vector database connectivity"""
    start = datetime.utcnow()
    try:
        await vector_store.health_check()
        duration = (datetime.utcnow() - start).total_seconds() * 1000
        return HealthCheck(
            name="vector_db",
            status=HealthStatus.HEALTHY,
            message="Vector DB connection successful",
            duration_ms=duration,
        )
    except Exception as e:
        duration = (datetime.utcnow() - start).total_seconds() * 1000
        return HealthCheck(
            name="vector_db",
            status=HealthStatus.UNHEALTHY,
            message=f"Vector DB connection failed: {str(e)}",
            duration_ms=duration,
        )


async def check_external_api(api_name: str, check_func: Callable) -> HealthCheck:
    """Check external API connectivity"""
    start = datetime.utcnow()
    try:
        await check_func()
        duration = (datetime.utcnow() - start).total_seconds() * 1000
        return HealthCheck(
            name=f"external_api_{api_name}",
            status=HealthStatus.HEALTHY,
            message=f"{api_name} API connection successful",
            duration_ms=duration,
        )
    except Exception as e:
        duration = (datetime.utcnow() - start).total_seconds() * 1000
        return HealthCheck(
            name=f"external_api_{api_name}",
            status=HealthStatus.DEGRADED,  # External APIs are often non-critical
            message=f"{api_name} API connection failed: {str(e)}",
            duration_ms=duration,
        )


async def check_disk_space(path: str = "/", threshold_percent: float = 90.0) -> HealthCheck:
    """Check disk space"""
    import shutil
    start = datetime.utcnow()
    try:
        total, used, free = shutil.disk_usage(path)
        used_percent = (used / total) * 100
        duration = (datetime.utcnow() - start).total_seconds() * 1000

        if used_percent >= threshold_percent:
            return HealthCheck(
                name="disk_space",
                status=HealthStatus.UNHEALTHY,
                message=f"Disk usage critical: {used_percent:.1f}%",
                details={"used_percent": used_percent, "free_gb": free / (1024**3)},
                duration_ms=duration,
            )
        elif used_percent >= threshold_percent * 0.8:
            return HealthCheck(
                name="disk_space",
                status=HealthStatus.DEGRADED,
                message=f"Disk usage high: {used_percent:.1f}%",
                details={"used_percent": used_percent, "free_gb": free / (1024**3)},
                duration_ms=duration,
            )
        else:
            return HealthCheck(
                name="disk_space",
                status=HealthStatus.HEALTHY,
                message=f"Disk usage normal: {used_percent:.1f}%",
                details={"used_percent": used_percent, "free_gb": free / (1024**3)},
                duration_ms=duration,
            )
    except Exception as e:
        duration = (datetime.utcnow() - start).total_seconds() * 1000
        return HealthCheck(
            name="disk_space",
            status=HealthStatus.UNHEALTHY,
            message=f"Disk check failed: {str(e)}",
            duration_ms=duration,
        )


async def check_memory(threshold_percent: float = 90.0) -> HealthCheck:
    """Check memory usage"""
    import psutil
    start = datetime.utcnow()
    try:
        memory = psutil.virtual_memory()
        used_percent = memory.percent
        duration = (datetime.utcnow() - start).total_seconds() * 1000

        if used_percent >= threshold_percent:
            return HealthCheck(
                name="memory",
                status=HealthStatus.UNHEALTHY,
                message=f"Memory usage critical: {used_percent:.1f}%",
                details={"used_percent": used_percent, "available_gb": memory.available / (1024**3)},
                duration_ms=duration,
            )
        elif used_percent >= threshold_percent * 0.8:
            return HealthCheck(
                name="memory",
                status=HealthStatus.DEGRADED,
                message=f"Memory usage high: {used_percent:.1f}%",
                details={"used_percent": used_percent, "available_gb": memory.available / (1024**3)},
                duration_ms=duration,
            )
        else:
            return HealthCheck(
                name="memory",
                status=HealthStatus.HEALTHY,
                message=f"Memory usage normal: {used_percent:.1f}%",
                details={"used_percent": used_percent, "available_gb": memory.available / (1024**3)},
                duration_ms=duration,
            )
    except Exception as e:
        duration = (datetime.utcnow() - start).total_seconds() * 1000
        return HealthCheck(
            name="memory",
            status=HealthStatus.UNHEALTHY,
            message=f"Memory check failed: {str(e)}",
            duration_ms=duration,
        )


# Global health checker
_health_checker: HealthChecker | None = None


def get_health_checker() -> HealthChecker:
    """Get global health checker"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


def init_health_checker(service_name: str = "ai-smart-city-concierge", version: str = "1.0.0") -> HealthChecker:
    """Initialize global health checker"""
    global _health_checker
    _health_checker = HealthChecker(service_name, version)
    return _health_checker
