from pydantic import BaseModel

class Course(BaseModel):
    id: str
    title: str
    description: str
    credits: int
    is_effective: bool = False
    likes: int = 0