from app.clients.networking.admin_service_networking_client import get_required_admin_service_client
from shared_backend.schemas.health import HealthRead


def read_health() -> HealthRead:
    return get_required_admin_service_client().read_health()
