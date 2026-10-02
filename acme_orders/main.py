from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .api import carts, catalog, discounts, orders, reporting
from .config import get_settings
from .db import init_db
from .errors import DomainError


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title=get_settings().app_name, version="0.1.0", lifespan=lifespan)
app.include_router(catalog.router)
app.include_router(discounts.router)
app.include_router(carts.router)
app.include_router(orders.router)
app.include_router(reporting.router)


@app.exception_handler(DomainError)
async def domain_error_handler(_request: Request, exc: DomainError):
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})


@app.get("/health")
def health():
    return {"status": "ok"}
