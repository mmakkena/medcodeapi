"""Custom database types for cross-database compatibility"""

import uuid
import json
from sqlalchemy import TypeDecorator, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID, JSONB as PostgreSQL_JSONB, TSVECTOR as PostgreSQL_TSVECTOR


class GUID(TypeDecorator):
    """
    Platform-independent GUID type.

    Uses PostgreSQL's UUID type when available, otherwise uses
    String(36) for SQLite and other databases.

    Stores UUIDs as strings in SQLite and as native UUID in PostgreSQL.
    """

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQL_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, str):
                return uuid.UUID(value)
            return value


class JSONB(TypeDecorator):
    """
    Platform-independent JSONB type.

    Uses PostgreSQL's JSONB type when available, otherwise uses
    Text with JSON serialization for SQLite and other databases.
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQL_JSONB)
        else:
            return dialect.type_descriptor(Text)

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            return json.loads(value) if value else None


class TSVECTOR(TypeDecorator):
    """
    Platform-independent TSVECTOR type for full-text search.

    Uses PostgreSQL's TSVECTOR type when available, otherwise uses
    Text for SQLite (full-text search features won't work in SQLite).
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQL_TSVECTOR)
        else:
            # For SQLite/testing, just store as Text
            return dialect.type_descriptor(Text)
