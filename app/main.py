from fastapi import FastAPI

from app.database import Base, engine
from app.errors import register_exception_handlers
from app.routers.categories import router as categories_router
from app.routers.tickets import router as tickets_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dorm Maintenance Ticket API", version="1.0.0")
register_exception_handlers(app)

app.include_router(categories_router)
app.include_router(tickets_router)


@app.get("/")
def healthcheck() -> dict[str, str]:
    return {"message": "Dorm Maintenance Ticket API is running"}
