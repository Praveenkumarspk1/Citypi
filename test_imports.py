import sys
sys.path.insert(0, 'apps/api/src')
from ai_smart_city_concierge.infrastructure.config.settings import get_settings
from ai_smart_city_concierge.infrastructure.config.database import Base
from ai_smart_city_concierge.infrastructure.persistence.sqlalchemy.models import user, poi, conversation, itinerary, transit, weather, media, feedback
print('Imports successful')
print('Base metadata tables:', list(Base.metadata.tables.keys()))