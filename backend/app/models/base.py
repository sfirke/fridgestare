from datetime import UTC, datetime

from sqlalchemy import DateTime, Dialect, TypeDecorator
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

MYSQL_DIALECTS = ("mysql", "mariadb")
NAIVE_DIALECTS = (*MYSQL_DIALECTS, "sqlite")


def utcnow() -> datetime:
    return datetime.now(tz=UTC)


class UtcDateTime(TypeDecorator):  # pylint: disable=abstract-method,too-many-ancestors
    """Datetime column that always round-trips as timezone-aware UTC.

    MariaDB's DATETIME carries no offset and SQLite stores whatever string it is
    given, so both hand back naive values. Normalizing here keeps the API layer
    emitting real UTC timestamps regardless of which backend is in use.

    The disables above are inherent to subclassing TypeDecorator: it leaves
    python_type and process_literal_param to the wrapped impl, and its own
    ancestry is deeper than the configured limit.
    """

    impl = DateTime
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect):
        if dialect.name in MYSQL_DIALECTS:
            return dialect.type_descriptor(mysql.DATETIME(fsp=6))
        return dialect.type_descriptor(DateTime(timezone=True))

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        value = value.astimezone(UTC)
        if dialect.name in NAIVE_DIALECTS:
            return value.replace(tzinfo=None)
        return value

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime,
        default=utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        UtcDateTime,
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )
