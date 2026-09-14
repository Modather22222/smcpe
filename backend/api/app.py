from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os

from .routers import auth, employees, fx, runs, reports, bank, payslips, statutory, audit, tenants

app = FastAPI(title="SMCPE API", version="2026.09", description="Sudan Multi-Currency Payroll Engine — COMP-3 exact via libpayroll.so")

origins = [o.strip() for o in os.getenv("CORS_ORIGIN", "https://pay.yourdomain.sd,http://localhost,http://127.0.0.1").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    # check lib
    lib_path = os.getenv("COBOL_LIB", "backend/cobol/libpayroll.so")
    import pathlib
    exists = pathlib.Path(lib_path).exists()
    return {"ok": True, "lib": "libpayroll.so", "lib_exists": exists, "version": "v2026.09", "stack": "FastAPI+COBOL COMP-3"}

@app.get("/api/me")
def me(request: Request):
    # stub, real via auth router require_user
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
    import time, uuid
    start = time.time()
    request_id = str(uuid.uuid4())[:8]
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(round(time.time()-start, 4))
    return response
