from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, #aliases in camelCase
        validate_by_name=True,
        validate_by_alias=True, 
    )


class Course(CamelModel):
    id: str
    title: str
    description: str
    credits: int
    is_effective: bool = False#в джейсон это будет isEffective
    likes: int = 0