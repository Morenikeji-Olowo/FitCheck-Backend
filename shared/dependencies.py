from fastapi import Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from uuid import UUID
from core.config.settings import settings
from core.auth.auth_service import verify_token
from shared.logger import get_logger
from shared.exceptions import FitCheckException

logger = get_logger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    user_id: UUID | None = Query(None)
) -> UUID:
    """
    Single source of truth for identifying the authenticated user.
    Every route uses this instead of trusting a client-supplied user_id.

    Production: Authorization: Bearer <token> is required.
    Development (DEV_AUTH_BYPASS=true): falls back to ?user_id=
    if no valid Bearer token is provided — keeps curl/Postman
    testing easy without weakening production behavior.
    """
    if credentials and credentials.credentials:
        token = credentials.credentials.strip()
        if token:
            verified_user_id = verify_token(token)
            try:
                return UUID(verified_user_id)
            except ValueError:
                raise FitCheckException(
                    "Invalid authentication token.",
                    code="INVALID_TOKEN", status_code=401
                )

    if settings.DEV_AUTH_BYPASS and user_id is not None:
        logger.warning(f"DEV_AUTH_BYPASS active — trusting user_id={user_id} from query param")
        return user_id

    raise FitCheckException(
        "Authentication required. Please log in.",
        code="UNAUTHORIZED", status_code=401
    )