from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

from routers import auth, quiz, classes, courses, teacher_courses, webhooks
from routers import user_types, professors

app = FastAPI(title="EDU_DRIM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["quiz"])
app.include_router(classes.router, prefix="/api/classes", tags=["classes"])
app.include_router(courses.router, prefix="/api/courses", tags=["courses"])
app.include_router(teacher_courses.router, prefix="/api/teacher/courses", tags=["teacher-courses"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(user_types.router, prefix="/api/user-types", tags=["user-types"])
app.include_router(professors.router, prefix="/api/professors", tags=["professors"])


@app.get("/health")
def health():
    return {"status": "ok"}
