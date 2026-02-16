from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

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


@app.get("/mock-ui", response_class=HTMLResponse)
def mock_ui() -> str:
    ui_path = Path(__file__).with_name("mock_ui.html")
    return ui_path.read_text(encoding="utf-8")
