from fastapi import FastAPI

from app.routers import health, photos

app = FastAPI(title="Photo Blog API")
app.include_router(health.router)
app.include_router(photos.router)
