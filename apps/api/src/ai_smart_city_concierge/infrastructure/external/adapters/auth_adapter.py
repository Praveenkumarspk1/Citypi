"""
Authentication Service Adapters
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from ....application.ports.external_services import AuthServicePort


@dataclass
class TokenPayload:
    """Token payload"""
    user_id: UUID
    claims: dict[str, Any]
    exp: datetime
    iat: datetime
    jti: str


class BaseAuthAdapter(AuthServicePort, ABC):
    """Base authentication adapter"""

    @abstractmethod
    async def _verify_token_request(self, token: str) -> TokenPayload | None:
        """Verify token request"""
        pass

    @abstractmethod
    async def _create_token_request(
        self,
        user_id: UUID,
        claims: dict[str, Any] | None,
        expires_in: int,
    ) -> str:
        """Create token request"""
        pass

    @abstractmethod
    async def _refresh_token_request(self, refresh_token: str) -> str | None:
        """Refresh token request"""
        pass

    @abstractmethod
    async def _revoke_token_request(self, token: str) -> None:
        """Revoke token request"""
        pass

    @abstractmethod
    async def _verify_oauth_token_request(
        self,
        provider: str,
        token: str,
    ) -> dict[str, Any] | None:
        """Verify OAuth token request"""
        pass

    async def verify_token(self, token: str) -> dict[str, Any] | None:
        """Verify JWT token"""
        payload = await self._verify_token_request(token)
        if payload:
            return {
                "user_id": str(payload.user_id),
                "claims": payload.claims,
                "exp": payload.exp.isoformat(),
                "iat": payload.iat.isoformat(),
                "jti": payload.jti,
            }
        return None

    async def create_token(
        self,
        user_id: UUID,
        claims: dict[str, Any] | None = None,
        expires_in: int = 3600,
    ) -> str:
        """Create JWT token"""
        return await self._create_token_request(user_id, claims, expires_in)

    async def refresh_token(self, refresh_token: str) -> str | None:
        """Refresh access token"""
        return await self._refresh_token_request(refresh_token)

    async def revoke_token(self, token: str) -> None:
        """Revoke token"""
        await self._revoke_token_request(token)

    async def verify_oauth_token(
        self,
        provider: str,
        token: str,
    ) -> dict[str, Any] | None:
        """Verify OAuth token"""
        return await self._verify_oauth_token_request(provider, token)


class JWTAuthAdapter(BaseAuthAdapter):
    """JWT authentication adapter"""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        issuer: str = "smart-city-concierge",
        audience: str = "smart-city-concierge-api",
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.issuer = issuer
        self.audience = audience
        self._revoked_tokens = set()  # In production, use Redis

    async def _verify_token_request(self, token: str) -> TokenPayload | None:
        import jwt

        try:
            # Check if token is revoked
            if token in self._revoked_tokens:
                return None

            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                audience=self.audience,
            )

            return TokenPayload(
                user_id=UUID(payload["sub"]),
                claims=payload.get("claims", {}),
                exp=datetime.fromtimestamp(payload["exp"]),
                iat=datetime.fromtimestamp(payload["iat"]),
                jti=payload["jti"],
            )
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    async def _create_token_request(
        self,
        user_id: UUID,
        claims: dict[str, Any] | None,
        expires_in: int,
    ) -> str:
        import uuid

        import jwt

        now = datetime.utcnow()
        exp = now + timedelta(seconds=expires_in)
        jti = str(uuid.uuid4())

        payload = {
            "sub": str(user_id),
            "claims": claims or {},
            "iat": now,
            "exp": exp,
            "jti": jti,
            "iss": self.issuer,
            "aud": self.audience,
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    async def _refresh_token_request(self, refresh_token: str) -> str | None:
        # Verify refresh token and create new access token
        payload = await self._verify_token_request(refresh_token)
        if not payload:
            return None

        # Check if it's a refresh token
        if payload.claims.get("type") != "refresh":
            return None

        # Create new access token
        return await self._create_token_request(
            payload.user_id,
            payload.claims,
            3600,  # 1 hour
        )

    async def _revoke_token_request(self, token: str) -> None:
        self._revoked_tokens.add(token)

    async def _verify_oauth_token_request(
        self,
        provider: str,
        token: str,
    ) -> dict[str, Any] | None:
        # JWT adapter doesn't handle OAuth
        return None


class FirebaseAuthAdapter(BaseAuthAdapter):
    """Firebase Authentication adapter"""

    def __init__(self, credentials_path: str, project_id: str):
        self.credentials_path = credentials_path
        self.project_id = project_id
        self._app = None

    async def _get_app(self):
        if self._app is None:
            import firebase_admin
            from firebase_admin import credentials

            cred = credentials.Certificate(self.credentials_path)
            self._app = firebase_admin.initialize_app(cred, {
                'projectId': self.project_id,
            })
        return self._app

    async def _verify_token_request(self, token: str) -> TokenPayload | None:
        try:
            from firebase_admin import auth

            decoded_token = auth.verify_id_token(token)

            return TokenPayload(
                user_id=UUID(decoded_token["uid"]),
                claims=decoded_token.get("claims", {}),
                exp=datetime.fromtimestamp(decoded_token["exp"]),
                iat=datetime.fromtimestamp(decoded_token["iat"]),
                jti=decoded_token.get("jti", ""),
            )
        except Exception:
            return None

    async def _create_token_request(
        self,
        user_id: UUID,
        claims: dict[str, Any] | None,
        expires_in: int,
    ) -> str:
        # Firebase doesn't support custom token creation with arbitrary claims
        # Use custom token
        from firebase_admin import auth

        custom_token = auth.create_custom_token(str(user_id), claims or {})
        return custom_token.decode()

    async def _refresh_token_request(self, refresh_token: str) -> str | None:
        # Firebase handles refresh internally
        return None

    async def _revoke_token_request(self, token: str) -> None:
        # Firebase doesn't support token revocation directly
        pass

    async def _verify_oauth_token_request(
        self,
        provider: str,
        token: str,
    ) -> dict[str, Any] | None:
        try:
            from firebase_admin import auth

            # Verify OAuth token with Firebase
            if provider == "google":
                user = auth.verify_id_token(token)
                return {
                    "user_id": user["uid"],
                    "email": user.get("email"),
                    "name": user.get("name"),
                    "picture": user.get("picture"),
                    "provider": "google",
                }
            elif provider == "facebook":
                # Would need Facebook OAuth verification
                pass
            elif provider == "apple":
                # Would need Apple OAuth verification
                pass
        except Exception:
            pass
        return None


class Auth0Adapter(BaseAuthAdapter):
    """Auth0 authentication adapter"""

    def __init__(
        self,
        domain: str,
        client_id: str,
        client_secret: str,
        audience: str,
    ):
        self.domain = domain
        self.client_id = client_id
        self.client_secret = client_secret
        self.audience = audience
        self._jwks = None

    async def _get_jwks(self):
        if self._jwks is None:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://{self.domain}/.well-known/jwks.json") as resp:
                    self._jwks = await resp.json()
        return self._jwks

    async def _verify_token_request(self, token: str) -> TokenPayload | None:
        import jwt
        from jwt.algorithms import RSAAlgorithm

        try:
            # Get JWKS
            jwks = await self._get_jwks()

            # Get key ID from token header
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")

            # Find matching key
            key = None
            for jwk in jwks["keys"]:
                if jwk["kid"] == kid:
                    key = RSAAlgorithm.from_jwk(json.dumps(jwk))
                    break

            if not key:
                return None

            payload = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=f"https://{self.domain}/",
            )

            return TokenPayload(
                user_id=UUID(payload["sub"]),
                claims=payload.get("claims", {}),
                exp=datetime.fromtimestamp(payload["exp"]),
                iat=datetime.fromtimestamp(payload["iat"]),
                jti=payload.get("jti", ""),
            )
        except Exception:
            return None

    async def _create_token_request(
        self,
        user_id: UUID,
        claims: dict[str, Any] | None,
        expires_in: int,
    ) -> str:
        # Auth0 doesn't support token creation from client
        # Would need to use client credentials flow
        return ""

    async def _refresh_token_request(self, refresh_token: str) -> str | None:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://{self.domain}/oauth/token",
                data={
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                },
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("access_token")
        return None

    async def _revoke_token_request(self, token: str) -> None:
        # Auth0 token revocation
        pass

    async def _verify_oauth_token_request(
        self,
        provider: str,
        token: str,
    ) -> dict[str, Any] | None:
        # Auth0 can verify tokens from various providers
        return await self._verify_token_request(token)


class SupabaseAuthAdapter(BaseAuthAdapter):
    """Supabase authentication adapter"""

    def __init__(self, url: str, anon_key: str, service_role_key: str):
        self.url = url
        self.anon_key = anon_key
        self.service_role_key = service_role_key
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from supabase import create_client
            self._client = create_client(self.url, self.service_role_key)
        return self._client

    async def _verify_token_request(self, token: str) -> TokenPayload | None:
        try:
            client = await self._get_client()
            user = client.auth.get_user(token)

            return TokenPayload(
                user_id=UUID(user.user.id),
                claims=user.user.user_metadata or {},
                exp=datetime.fromtimestamp(user.user.exp),
                iat=datetime.fromtimestamp(user.user.iat),
                jti=user.user.id,
            )
        except Exception:
            return None

    async def _create_token_request(
        self,
        user_id: UUID,
        claims: dict[str, Any] | None,
        expires_in: int,
    ) -> str:
        client = await self._get_client()

        # Generate custom token
        response = client.auth.admin.generate_link({
            "type": "magiclink",
            "email": claims.get("email", "") if claims else "",
        })

        return response.properties.get("action_link", "")

    async def _refresh_token_request(self, refresh_token: str) -> str | None:
        client = await self._get_client()

        response = client.auth.refresh_session(refresh_token)
        return response.session.access_token if response.session else None

    async def _revoke_token_request(self, token: str) -> None:
        # Supabase doesn't have direct token revocation
        pass

    async def _verify_oauth_token_request(
        self,
        provider: str,
        token: str,
    ) -> dict[str, Any] | None:
        try:
            client = await self._get_client()

            if provider == "google":
                response = client.auth.sign_in_with_oauth({
                    "provider": "google",
                    "access_token": token,
                })
                return {
                    "user_id": response.user.id,
                    "email": response.user.email,
                    "name": response.user.user_metadata.get("full_name"),
                    "picture": response.user.user_metadata.get("avatar_url"),
                    "provider": "google",
                }
        except Exception:
            pass
        return None
