# backend/app/repositories/base_repository.py
"""
Base Repository Implementation

Provides a generic repository pattern with common CRUD operations that can be
extended by specific repositories for each domain model.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, desc, asc
import logging

logger = logging.getLogger(__name__)

# Generic type for model classes
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseRepository(Generic[ModelType], ABC):
    """
    Base repository class providing common CRUD operations.
    
    This abstract base class defines the standard interface for all repositories
    and provides default implementations for common operations.
    """

    def __init__(self, model: Type[ModelType], db: Session):
        """
        Initialize repository with model class and database session.
        
        Args:
            model: SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db

    def get(self, id: Any) -> Optional[ModelType]:
        """
        Get a single record by ID.
        
        Args:
            id: Primary key value
            
        Returns:
            Model instance or None if not found
        """
        try:
            return self.db.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} with id {id}: {e}")
            raise

    def get_by(self, **kwargs) -> Optional[ModelType]:
        """
        Get a single record by arbitrary field values.
        
        Args:
            **kwargs: Field-value pairs to filter by
            
        Returns:
            Model instance or None if not found
        """
        try:
            query = self.db.query(self.model)
            for field, value in kwargs.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
                else:
                    logger.warning(f"Field {field} not found in {self.model.__name__}")
            return query.first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} with filters {kwargs}: {e}")
            raise

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        desc_order: bool = False,
        **filters
    ) -> List[ModelType]:
        """
        Get multiple records with pagination and filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Field name to order by
            desc_order: Whether to use descending order
            **filters: Field-value pairs to filter by
            
        Returns:
            List of model instances
        """
        try:
            query = self.db.query(self.model)
            
            # Apply filters
            for field, value in filters.items():
                if hasattr(self.model, field):
                    if isinstance(value, list):
                        # Handle IN clause for lists
                        query = query.filter(getattr(self.model, field).in_(value))
                    else:
                        query = query.filter(getattr(self.model, field) == value)
                else:
                    logger.warning(f"Field {field} not found in {self.model.__name__}")
            
            # Apply ordering
            if order_by and hasattr(self.model, order_by):
                order_field = getattr(self.model, order_by)
                if desc_order:
                    query = query.order_by(desc(order_field))
                else:
                    query = query.order_by(asc(order_field))
            
            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} records: {e}")
            raise

    def count(self, **filters) -> int:
        """
        Count records matching the given filters.
        
        Args:
            **filters: Field-value pairs to filter by
            
        Returns:
            Number of matching records
        """
        try:
            query = self.db.query(self.model)
            
            # Apply filters
            for field, value in filters.items():
                if hasattr(self.model, field):
                    if isinstance(value, list):
                        query = query.filter(getattr(self.model, field).in_(value))
                    else:
                        query = query.filter(getattr(self.model, field) == value)
            
            return query.count()
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.model.__name__} records: {e}")
            raise

    def create(self, obj_in: Union[CreateSchemaType, Dict[str, Any]]) -> ModelType:
        """
        Create a new record.
        
        Args:
            obj_in: Data for creating the record (Pydantic model or dict)
            
        Returns:
            Created model instance
        """
        try:
            if hasattr(obj_in, 'model_dump'):
                # Pydantic model
                obj_data = obj_in.model_dump(exclude_unset=True)
            elif hasattr(obj_in, 'dict'):
                # Legacy Pydantic model
                obj_data = obj_in.dict(exclude_unset=True)
            else:
                # Dictionary
                obj_data = obj_in
            
            db_obj = self.model(**obj_data)
            self.db.add(db_obj)
            self.db.flush()  # Flush to get the ID without committing
            self.db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            logger.error(f"Error creating {self.model.__name__}: {e}")
            self.db.rollback()
            raise

    def update(
        self,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update an existing record.
        
        Args:
            db_obj: Existing model instance
            obj_in: Data for updating the record
            
        Returns:
            Updated model instance
        """
        try:
            if hasattr(obj_in, 'model_dump'):
                # Pydantic model
                update_data = obj_in.model_dump(exclude_unset=True)
            elif hasattr(obj_in, 'dict'):
                # Legacy Pydantic model
                update_data = obj_in.dict(exclude_unset=True)
            else:
                # Dictionary
                update_data = obj_in

            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            self.db.flush()
            self.db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            logger.error(f"Error updating {self.model.__name__}: {e}")
            self.db.rollback()
            raise

    def delete(self, id: Any) -> bool:
        """
        Delete a record by ID.
        
        Args:
            id: Primary key value
            
        Returns:
            True if record was deleted, False if not found
        """
        try:
            obj = self.db.query(self.model).filter(self.model.id == id).first()
            if obj:
                self.db.delete(obj)
                self.db.flush()
                return True
            return False
        except SQLAlchemyError as e:
            logger.error(f"Error deleting {self.model.__name__} with id {id}: {e}")
            self.db.rollback()
            raise

    def delete_by(self, **kwargs) -> int:
        """
        Delete multiple records matching the given filters.
        
        Args:
            **kwargs: Field-value pairs to filter by
            
        Returns:
            Number of deleted records
        """
        try:
            query = self.db.query(self.model)
            for field, value in kwargs.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
            
            count = query.count()
            query.delete()
            self.db.flush()
            return count
        except SQLAlchemyError as e:
            logger.error(f"Error deleting {self.model.__name__} records: {e}")
            self.db.rollback()
            raise

    def exists(self, **kwargs) -> bool:
        """
        Check if a record exists matching the given filters.
        
        Args:
            **kwargs: Field-value pairs to filter by
            
        Returns:
            True if record exists, False otherwise
        """
        try:
            query = self.db.query(self.model)
            for field, value in kwargs.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
            
            return query.first() is not None
        except SQLAlchemyError as e:
            logger.error(f"Error checking existence in {self.model.__name__}: {e}")
            raise

    @abstractmethod
    def get_domain_specific_methods(self) -> Dict[str, Any]:
        """
        Return domain-specific methods for this repository.
        
        This method should be implemented by each concrete repository
        to provide access to specialized query methods.
        
        Returns:
            Dictionary of method names and their implementations
        """
        pass

    def bulk_create(self, objects: List[Dict[str, Any]]) -> List[ModelType]:
        """
        Create multiple records in a single operation.
        
        Args:
            objects: List of data dictionaries
            
        Returns:
            List of created model instances
        """
        try:
            db_objects = [self.model(**obj_data) for obj_data in objects]
            self.db.add_all(db_objects)
            self.db.flush()
            for obj in db_objects:
                self.db.refresh(obj)
            return db_objects
        except SQLAlchemyError as e:
            logger.error(f"Error bulk creating {self.model.__name__} records: {e}")
            self.db.rollback()
            raise

    def bulk_update(self, updates: List[Dict[str, Any]]) -> bool:
        """
        Update multiple records in a single operation.
        
        Args:
            updates: List of update dictionaries with 'id' and update fields
            
        Returns:
            True if operation succeeded
        """
        try:
            for update_data in updates:
                record_id = update_data.pop('id')
                self.db.query(self.model).filter(self.model.id == record_id).update(update_data)
            
            self.db.flush()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error bulk updating {self.model.__name__} records: {e}")
            self.db.rollback()
            raise