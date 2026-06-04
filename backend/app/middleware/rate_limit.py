"""Redis-backed rate limiting (Story O.2).

Rates:
  - External ingestion API: 100 req/min per API key
  - Member redemption:       10 req/hour per member ID
"""

from slowapi import Limiter
from slowapi.util import get_remote_address


def _api_key_identifier(request) -> str:
    """Use X-API-Key header as identifier for external app rate limits."""
    return request.headers.get("X-API-Key", get_remote_address(request))


def _member_identifier(request) -> str:
    """Use authenticated member ID (injected into request.state) or IP fallback."""
    return getattr(request.state, "member_id", None) or get_remote_address(request)


# Global limiter — storage URI is configured in app factory via app.state.limiter
limiter = Limiter(key_func=get_remote_address)
