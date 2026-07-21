from core.storage.supabase_client import supabase
from shared.logger import get_logger
from shared.exceptions import FitCheckException

logger = get_logger(__name__)


def verify_token(jwt_token: str) -> str:
    """
    Verifies a Supabase JWT and returns the authenticated user's ID.
    Uses Supabase's own auth verification — not manual JWT decoding —
    so signature checking, expiration, and revocation are all handled
    by Supabase directly.
    """
    try:
        response = supabase.auth.get_user(jwt_token)
        user = getattr(response, "user", None)

        if not user:
            raise FitCheckException(
                "Invalid or expired session. Please log in again.",
                code="INVALID_TOKEN", status_code=401
            )

        user_id = user.id
        logger.debug(f"Token verified — user={user_id}")
        return user_id

    except FitCheckException:
        raise
    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        raise FitCheckException(
            "Invalid or expired session. Please log in again.",
            code="INVALID_TOKEN", status_code=401
        )