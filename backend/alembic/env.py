from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy import types as sa_types
from sqlalchemy.dialects.mysql import LONGTEXT

from app.core.config import get_settings
from app.db.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)
target_metadata = Base.metadata


def compare_type(_context, _inspected_column, _metadata_column, inspected_type, metadata_type):
    """Suppress false-positive type diffs that are artifacts of MariaDB reflection.

    MariaDB implements JSON as LONGTEXT plus a json_valid() CHECK constraint, so a
    reflected JSON column comes back as text and cannot be distinguished from one.
    Returning None for everything else defers to Alembic's default comparison.
    """
    if isinstance(metadata_type, sa_types.JSON) and isinstance(inspected_type, LONGTEXT | sa_types.Text):
        return False
    return None


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=compare_type,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=compare_type,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
