import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool

from alembic import context

# Add the project root to Python path so we can import the package
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import our models and settings from the installed package
# The package is installed in editable mode from the project root
from ai_smart_city_concierge.infrastructure.config.settings import get_settings
from ai_smart_city_concierge.infrastructure.config.database import Base

# Import all models to register them with Base.metadata
from ai_smart_city_concierge.infrastructure.persistence.sqlalchemy.models import (
    user, poi, conversation, itinerary, transit, weather, media, feedback
)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# Override sqlalchemy.url from settings - use SQLite for migration generation
# This allows autogenerate to work without a running PostgreSQL server
config.set_main_option("sqlalchemy.url", "sqlite:///./test_migration.db")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    from sqlalchemy import create_engine
    
    # Use SQLite for migration generation
    connectable = create_engine("sqlite:///./test_migration.db", poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
