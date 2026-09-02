"""
Security Settings

Configuration for authentication, authorization, and security.
"""
from typing import List
from pydantic import Field
from .base import BaseSettings


class SecuritySettings(BaseSettings):
    """Security configuration."""
    
    # JWT
    jwt_secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        validation_alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "smart-city-concierge"
    jwt_audience: str = "smart-city-concierge-users"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    jwt_private_key: str = ""
    jwt_public_key: str = ""

    # API Keys
    api_key_prefix: str = "sk_"
    api_key_length: int = 32
    api_key_hash_algorithm: str = "sha256"

    # Password
    password_min_length: int = 8
    password_max_length: int = 128
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    password_bcrypt_rounds: int = 12

    # Email verification
    email_verification_token_expire_hours: int = 24
    email_verification_url: str = "https://app.example.com/verify-email"

    # Password reset
    password_reset_token_expire_hours: int = 1
    password_reset_url: str = "https://app.example.com/reset-password"

    # Session
    session_cookie_name: str = "session"
    session_cookie_secure: bool = True
    session_cookie_httponly: bool = True
    session_cookie_samesite: str = "lax"
    session_expire_minutes: int = 60
    session_refresh_threshold_minutes: int = 5

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_storage: str = "redis"  # redis, memory
    rate_limit_default_limit: int = 100
    rate_limit_default_window: int = 60  # seconds

    # CORS
    cors_allow_origins: List[str] = Field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: List[str] = Field(default_factory=lambda: ["*"])
    cors_expose_headers: List[str] = Field(default_factory=list)
    cors_max_age: int = 86400

    # CSRF
    csrf_enabled: bool = True
    csrf_secret_key: str = Field(default="", validation_alias="CSRF_SECRET_KEY")
    csrf_cookie_name: str = "csrf_token"
    csrf_header_name: str = "X-CSRF-Token"

    # Security headers
    security_headers_enabled: bool = True
    hsts_max_age: int = 31536000
    hsts_include_subdomains: bool = True
    hsts_preload: bool = True
    csp_policy: str = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' wss: https:; frame-ancestors 'none';"
    referrer_policy: str = "strict-origin-when-cross-origin"
    permissions_policy: str = "geolocation=(), microphone=(), camera=()"

    # Encryption
    encryption_key: str = Field(default="", validation_alias="ENCRYPTION_KEY")
    encryption_algorithm: str = "AES-256-GCM"

    # Audit logging
    audit_log_enabled: bool = True
    audit_log_sensitive_fields: List[str] = Field(default_factory=lambda: ["password", "token", "secret", "key", "authorization"])