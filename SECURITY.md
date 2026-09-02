# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |

## Reporting a Vulnerability

Please report security vulnerabilities by opening a GitHub issue with the "security" label.

## Security Measures

- **Authentication**: JWT with refresh token rotation
- **Authorization**: RBAC with role-based permissions
- **Encryption**: TLS 1.3 in transit, AES-256 at rest
- **Input Validation**: Pydantic v2 on all endpoints
- **Rate Limiting**: Redis-based token bucket
- **Secrets Management**: Environment variables + GitHub Secrets

## Dependencies

We use Dependabot to keep dependencies updated. Security scans run on every PR via GitHub Actions.
