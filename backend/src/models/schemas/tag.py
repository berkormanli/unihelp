from src.models.schemas.base import BaseSchemaModel

class TagResponse(BaseSchemaModel):
    id: int
    name: str

class TagCreate(BaseSchemaModel):
    name: str