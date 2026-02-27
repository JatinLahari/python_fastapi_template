from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.database import connect_db, close_db
from routers import auth_router, user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(
    title="EduSphere API",
    description=(
        "Complete authentication & authorisation template using FastAPI + MongoDB.\n\n"
        "## Roles\n"
        "- **student** — Default role for learners\n"
        "- **academy_admin** — Manages a specific academy\n"
        "- **super_admin** — Full platform access\n\n"
        "## Auth Flow\n"
        "1. `POST /auth/register` → create account\n"
        "2. `POST /auth/login` → receive `access_token` + `refresh_token`\n"
        "3. Add `Authorization: Bearer <access_token>` header to protected endpoints\n"
        "4. `POST /auth/refresh` → exchange refresh token for a new access token\n"
        "5. `POST /auth/logout` → delete tokens from client storage\n"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)


@app.get("/", tags=["Health"], summary="API health check")
async def root():
    return {"status": "ok", "message": "EduSphere API is running 🚀", "docs": "/docs"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
