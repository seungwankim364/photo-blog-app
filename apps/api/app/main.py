from fastapi import FastAPI

from app.routers import health

app = FastAPI(title="Photo Blog API")
app.include_router(health.router)
