"""SMCPE API — FastAPI + COBOL COMP-3, centralized config, structured logging, global error handling."""
import pathlib
import time
import uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .config import settings
from .logging_conf import setup_logging, logger
from .routers import auth, employees, fx, runs, reports, bank, payslips, statutory, audit, tenants

setup_logging()

app = FastAPI(
    title="SMCPE API",
    version="2026.09",
    description="Sudan Multi-Currency Payroll Engine — COMP-3 exact via libpayroll.so",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exc_handler(request: Request, exc: HTTPException):
    logger.warning("HTTP %s %s -> %s %s", request.method, request.url.path, exc.status_code, exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception):
    logger.exception("Unhandled %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

@app.get("/api/health")
def health() -> dict:
    lib_path = pathlib.Path(settings.COBOL_LIB)
    return {
        "ok": True,
        "lib": "libpayroll.so",
        "lib_exists": lib_path.exists(),
        "version": settings.STATUTORY_VERSION,
        "stack": "FastAPI+COBOL COMP-3",
        "env": settings.ENV,
    }

@app.get("/api/me")
def me(request: Request) -> dict:
    return {"ok": True}

app.include_router(auth.router)
app.include_router(tenants.router)
app.include_router(employees.router)
app.include_router(fx.router)
app.include_router(runs.router)
app.include_router(reports.router)
app.include_router(bank.router)
app.include_router(payslips.router)
app.include_router(statutory.router)
app.include_router(audit.router)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    start = time.time()
    request_id = str(uuid.uuid4())[:8]
    # propagate to logger via context (simple: add to headers)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(round(time.time() - start, 4))
    # log with status
    logger.info("%s %s -> %s [%.4fs] id=%s", request.method, request.url.path, response.status_code, time.time() - start, request_id)
    return response
