from fastapi import FastAPI

from app.routes.health import router as health_router
from app.routes.imports import router as imports_router
from app.routes.razorpay import router as razorpay_router
from app.routes.reconcile import router as reconcile_router
from app.routes.runs import router as runs_router

app = FastAPI(title="Reconra API")
app.include_router(health_router)
app.include_router(imports_router)
app.include_router(reconcile_router)
app.include_router(razorpay_router)
app.include_router(runs_router)
