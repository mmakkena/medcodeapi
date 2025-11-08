"""Custom database types for cross-database compatibility"""

import uuid
import json
from sqlalchemy import TypeDecorator, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID, JSONB as PostgreSQL_JSONB, TSVECTOR as PostgreSQL_TSVECTOR

# Import pgvector type for vector embeddings
try:
    from pgvector.sqlalchemy import Vector as PostgreSQL_VECTOR
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False


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


class VECTOR(TypeDecorator):
    """
    Platform-independent VECTOR type for pgvector embeddings.

    Uses PostgreSQL's vector type from pgvector extension when available,
    otherwise uses Text with JSON serialization for SQLite/testing.

    Usage:
        embedding = Column(VECTOR(768))  # 768-dimensional vector
    """

    impl = Text
    cache_ok = True

    def __init__(self, dim=768):
        """Initialize with vector dimension (default 768 for MedCPT)"""
        self.dim = dim
        super().__init__()

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql' and PGVECTOR_AVAILABLE:
            return dialect.type_descriptor(PostgreSQL_VECTOR(self.dim))
        else:
            # For SQLite/testing or when pgvector not installed, store as JSON text
            return dialect.type_descriptor(Text)

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql' and PGVECTOR_AVAILABLE:
            # pgvector handles the conversion
            return value
        else:
            # Store as JSON string for SQLite
            if isinstance(value, (list, tuple)):
                return json.dumps(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql' and PGVECTOR_AVAILABLE:
            # pgvector returns as list
            return value
        else:
            # Parse JSON for SQLite
            if isinstance(value, str):
                return json.loads(value)
            return value
