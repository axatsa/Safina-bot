from typing import Generic, TypeVar, Type, List, Optional, Any, Union
from sqlalchemy.orm import Session
from pydantic import BaseModel
from sqlalchemy.inspection import inspect

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = obj_in.dict(exclude_unset=True)
        # Handle project_ids and branch_ids if they exist in schema but not in model directly
        # These are usually handled by specific repositories but we can do a basic check here
        # or just exclude them and handle in subclasses
        
        # Get model columns to avoid passing extra fields
        mapper = inspect(self.model)
        columns = [c.key for c in mapper.attrs]
        
        model_data = {k: v for k, v in obj_in_data.items() if k in columns}
        db_obj = self.model(**model_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, dict]
    ) -> ModelType:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
            
        mapper = inspect(self.model)
        columns = [c.key for c in mapper.attrs]
        
        for field in update_data:
            if field in columns:
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: Any) -> ModelType:
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj
