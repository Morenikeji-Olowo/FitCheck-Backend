from supabase import create_client
from core.config.settings import settings
from shared.logger import get_logger

logger = get_logger(__name__)

supabase = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_KEY
)