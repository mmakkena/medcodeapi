"""
Base Repository Pattern

Provides a generic repository base class for database operations.
Implements common CRUD operations with type safety.
"""

import logging
from typing import TypeVar, Generic, Type, List, Optional, Any, Dict
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from infrastructure.db.postgres import Base

logger = logging.getLogger(__name__)

# Type variable for the model class
T = TypeVar('T', bound=Base)


class BaseRepository(Generic[T]):
    """
    Generic repository base class.

    Provides common CRUD operations for SQLAlchemy models.
    Subclasses can override methods for custom behavior.
    """

    def __init__(self, model_class: Type[T], db: Session):
        """
        Initialize repository.

        Args:
            model_class: SQLAlchemy model class
            db: Database session
        """
        self.model_class = model_class
        self.db = db

    def get_by_id(self, id: UUID) -> Optional[T]:
        """
        Get a single record by ID.

        Args:
            id: Record UUID

        Returns:
            Model instance or None if not found
        """
        return self.db.query(self.model_class).filter(
            self.model_class.id == id
        ).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        descending: bool = False
    ) -> List[T]:
        """
        Get all records with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            order_by: Column name to order by
            descending: Sort descending if True

        Returns:
            List of model instances
        """
        query = self.db.query(self.model_class)

        if order_by and hasattr(self.model_class, order_by):
            column = getattr(self.model_class, order_by)
            query = query.order_by(column.desc() if descending else column)

        return query.offset(skip).limit(limit).all()

    def get_by_field(
        self,
        field_name: str,
        value: Any,
        limit: Optional[int] = None
    ) -> List[T]:
        """
        Get records by a specific field value.

        Args:
            field_name: Name of the field to filter by
            value: Value to match
            limit: Optional limit on results

        Returns:
            List of matching model instances
        """
        if not hasattr(self.model_class, field_name):
            raise ValueError(f"Model has no field '{field_name}'")

        query = self.db.query(self.model_class).filter(
            getattr(self.model_class, field_name) == value
        )

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_first_by_field(self, field_name: str, value: Any) -> Optional[T]:
        """
        Get first record matching a field value.

        Args:
            field_name: Name of the field to filter by
            value: Value to match

        Returns:
            First matching model instance or None
        """
        results = self.get_by_field(field_name, value, limit=1)
        return results[0] if results else None

    def create(self, obj_data: Dict[str, Any]) -> T:
        """
        Create a new record.

        Args:
            obj_data: Dictionary of field values

        Returns:
            Created model instance
        """
        db_obj = self.model_class(**obj_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, id: UUID, obj_data: Dict[str, Any]) -> Optional[T]:
        """
        Update a record by ID.

        Args:
            id: Record UUID
            obj_data: Dictionary of fields to update

        Returns:
            Updated model instance or None if not found
        """
        db_obj = self.get_by_id(id)
        if db_obj is None:
            return None

        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: UUID) -> bool:
        """
        Delete a record by ID.

        Args:
            id: Record UUID

        Returns:
            True if deleted, False if not found
        """
        db_obj = self.get_by_id(id)
        if db_obj is None:
            return False

        self.db.delete(db_obj)
        self.db.commit()
        return True

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records, optionally with filters.

        Args:
            filters: Optional dictionary of field=value filters

        Returns:
            Count of matching records
        """
        query = self.db.query(self.model_class)

        if filters:
            conditions = []
            for field, value in filters.items():
                if hasattr(self.model_class, field):
                    conditions.append(getattr(self.model_class, field) == value)
            if conditions:
                query = query.filter(and_(*conditions))

        return query.count()

    def exists(self, id: UUID) -> bool:
        """
        Check if a record exists.

        Args:
            id: Record UUID

        Returns:
            True if exists
        """
        return self.db.query(
            self.db.query(self.model_class).filter(
                self.model_class.id == id
            ).exists()
        ).scalar()

    def bulk_create(self, obj_list: List[Dict[str, Any]]) -> List[T]:
        """
        Create multiple records at once.

        Args:
            obj_list: List of dictionaries with field values

        Returns:
            List of created model instances
        """
        db_objs = [self.model_class(**data) for data in obj_list]
        self.db.add_all(db_objs)
        self.db.commit()

        for obj in db_objs:
            self.db.refresh(obj)

        return db_objs

    def search(
        self,
        search_fields: List[str],
        search_term: str,
        limit: int = 100
    ) -> List[T]:
        """
        Search records across multiple fields (case-insensitive).

        Args:
            search_fields: List of field names to search
            search_term: Term to search for
            limit: Maximum results to return

        Returns:
            List of matching model instances
        """
        conditions = []
        search_pattern = f"%{search_term}%"

        for field_name in search_fields:
            if hasattr(self.model_class, field_name):
                field = getattr(self.model_class, field_name)
                conditions.append(field.ilike(search_pattern))

        if not conditions:
            return []

        return self.db.query(self.model_class).filter(
            or_(*conditions)
        ).limit(limit).all()
