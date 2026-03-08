from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import books, loans, reservations, fines, reviews, users, api_keys, webhooks, cron

app = FastAPI(title="PageTurn API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        settings.frontend_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(books.router, tags=["books"])
app.include_router(loans.router, tags=["loans"])
app.include_router(reservations.router, tags=["reservations"])
app.include_router(fines.router, tags=["fines"])
app.include_router(reviews.router, tags=["reviews"])
app.include_router(users.router, tags=["users"])
app.include_router(api_keys.router, tags=["api-keys"])
app.include_router(webhooks.router, tags=["webhooks"])
app.include_router(cron.router, tags=["cron"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
