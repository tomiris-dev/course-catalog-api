from fastapi import FastAPI, HTTPException, Depends
from data import find_course, get_all_courses
from models import Course


app = FastAPI(title="Course Catalog API")

def pagination(page: int = 1, page_size: int = 20) -> dict:
    return {"offset": (page - 1) * page_size, "limit": page_size}

@app.get("/")
def read_root():
    return {"message": "Course Catalog API is running"}

@app.get("/courses", response_model=list[Course])
def list_courses(
    is_effective: bool | None = None,
    sort: str = "popular",
    p: dict = Depends(pagination),
):
    courses = get_all_courses()
    #Фильтрация
    if is_effective is not None:
        courses = [c for c in courses if c.is_effective == is_effective]
    #Сортировка
    if sort == "title":
        courses = sorted(courses, key=lambda c: c.title)
    else:
        courses = sorted(courses, key=lambda c: c.likes, reverse=True)
    #Пагинация
    offset = p["offset"]
    limit = p["limit"]
    return courses[offset : offset + limit]

@app.get("/courses/{course_id}", response_model=Course)
def get_course(course_id: str):
    course = find_course(course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course