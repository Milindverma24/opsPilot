import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apps.api.app.core.config import settings
from apps.api.app.core.database_init import init_db
from apps.api.app.api.v1.auth import router as auth_router
from apps.api.app.api.v1.dashboard import router as dashboard_router
from apps.api.app.api.v1.events import router as events_router
from apps.api.app.api.v1.documents import router as documents_router
from apps.api.app.api.v1.workflows import router as workflows_router
from apps.api.app.api.v1.approvals import router as approvals_router
from apps.api.app.api.v1.agents import router as agents_router
from apps.api.app.api.v1.policies import router as policies_router
from apps.api.app.api.v1.knowledge import router as knowledge_router
from apps.api.app.api.v1.audit import router as audit_router
from apps.api.app.api.v1.command import router as command_router
from apps.api.app.api.v1.test_lab import router as test_lab_router
from apps.api.app.api.v1.invoices import router as invoices_router
from apps.api.app.api.v1.users import router as users_router
from apps.api.app.api.v1.roles import router as roles_router
from apps.api.app.api.v1.organization import router as organization_router
from apps.api.app.api.v1.products import router as products_router
from apps.api.app.api.v1.categories import router as categories_router
from apps.api.app.api.v1.inventory import router as inventory_router
from apps.api.app.api.v1.warehouses import router as warehouses_router
from apps.api.app.api.v1.customers import router as customers_router
from apps.api.app.api.v1.orders import router as orders_router
from apps.api.app.api.v1.payments import router as payments_router
from apps.api.app.api.v1.shipments import router as shipments_router
from apps.api.app.api.v1.returns import router as returns_router
from apps.api.app.api.v1.refunds import router as refunds_router
from apps.api.app.api.v1.coupons import router as coupons_router
from apps.api.app.api.v1.support import router as support_router
from apps.api.app.api.v1.websites import router as websites_router
from apps.api.app.api.v1.emails import router as emails_router
from apps.api.app.api.v1.imports import router as imports_router
from apps.api.app.api.v1.agent_runs import router as agent_runs_router
from apps.api.app.api.v1.tools import router as tools_router

from apps.api.app.api.v1.escalations import router as escalations_router
from apps.api.app.api.v1.customer_ai import router as customer_ai_router
from apps.api.app.api.v1.command_center import router as command_center_router
from apps.api.app.api.v1.alerts import router as alerts_router
from apps.api.app.api.v1.observability import router as observability_router
from apps.api.app.api.v1.memory import router as memory_router
from apps.api.app.api.v1.feedback import router as feedback_router
from apps.api.app.api.v1.learning import router as learning_router
from apps.api.app.api.v1.security import router as security_router
from apps.api.app.api.v1.tasks import router as tasks_router
from apps.api.app.api.v1.purchase_orders import router as purchase_orders_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist
    init_db()
    # Startup: safely recover interrupted workflows & stale worker task leases
    try:
        from apps.api.app.core.database import SessionLocal
        from apps.api.app.services.recovery_manager import RecoveryManager
        rec_db = SessionLocal()
        RecoveryManager.run_startup_recovery(rec_db)
        rec_db.close()
    except Exception:
        pass
    yield
    # Shutdown


app = FastAPI(
    title="OpsPilot - Autonomous Business Operations Platform",
    description=(
        "Production-grade autonomous AI operations engine for business workflows. "
        "Coordinates multi-agent document intelligence, strict policy enforcement, "
        "human-in-the-loop approvals, controlled tool execution, and an immutable audit trail."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
for o in settings.cors_origin_list:
    if o not in origins:
        origins.append(o)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID & Observability Middleware
@app.middleware("http")
async def add_observability_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    start_time = time.time()

    response = await call_next(request)

    process_time = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = str(process_time)
    return response


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "path": request.url.path
        }
    )


# Mount v1 Routers
api_v1_prefix = "/api/v1"
app.include_router(auth_router, prefix=api_v1_prefix)
app.include_router(dashboard_router, prefix=api_v1_prefix)
app.include_router(events_router, prefix=api_v1_prefix)
app.include_router(documents_router, prefix=api_v1_prefix)
app.include_router(workflows_router, prefix=api_v1_prefix)
app.include_router(approvals_router, prefix=api_v1_prefix)
app.include_router(agent_runs_router, prefix=api_v1_prefix)
app.include_router(agents_router, prefix=api_v1_prefix)
app.include_router(policies_router, prefix=api_v1_prefix)
app.include_router(knowledge_router, prefix=api_v1_prefix)
app.include_router(audit_router, prefix=api_v1_prefix)
app.include_router(command_router, prefix=api_v1_prefix)
app.include_router(test_lab_router, prefix=api_v1_prefix)
app.include_router(invoices_router, prefix=api_v1_prefix)
app.include_router(users_router, prefix=api_v1_prefix)
app.include_router(roles_router, prefix=api_v1_prefix)
app.include_router(organization_router, prefix=api_v1_prefix)
app.include_router(products_router, prefix=api_v1_prefix)
app.include_router(categories_router, prefix=api_v1_prefix)
app.include_router(inventory_router, prefix=api_v1_prefix)
app.include_router(warehouses_router, prefix=api_v1_prefix)
app.include_router(customers_router, prefix=api_v1_prefix)
app.include_router(orders_router, prefix=api_v1_prefix)
app.include_router(payments_router, prefix=api_v1_prefix)
app.include_router(shipments_router, prefix=api_v1_prefix)
app.include_router(returns_router, prefix=api_v1_prefix)
app.include_router(refunds_router, prefix=api_v1_prefix)
app.include_router(coupons_router, prefix=api_v1_prefix)
app.include_router(support_router, prefix=api_v1_prefix)
app.include_router(websites_router, prefix=api_v1_prefix)
app.include_router(emails_router, prefix=api_v1_prefix)
app.include_router(imports_router, prefix=api_v1_prefix)
app.include_router(agent_runs_router, prefix=api_v1_prefix)
app.include_router(tools_router, prefix=api_v1_prefix)
app.include_router(escalations_router, prefix=api_v1_prefix)
app.include_router(customer_ai_router, prefix=api_v1_prefix)
app.include_router(command_center_router, prefix=api_v1_prefix)
app.include_router(alerts_router, prefix=api_v1_prefix)
app.include_router(observability_router, prefix=api_v1_prefix)
app.include_router(memory_router, prefix=api_v1_prefix)
app.include_router(feedback_router, prefix=api_v1_prefix)
app.include_router(learning_router, prefix=api_v1_prefix)
app.include_router(security_router, prefix=api_v1_prefix)
app.include_router(tasks_router, prefix=api_v1_prefix)
app.include_router(purchase_orders_router, prefix=api_v1_prefix)



@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


from sqlalchemy import text
from apps.api.app.core.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends


@app.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    redis_status = "ok"
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL, socket_timeout=0.5)
        r.ping()
    except Exception:
        # In local development without redis running, eager celery operates in-process
        redis_status = "ok" if settings.APP_ENV in ["development", "test"] else "degraded"

    overall_status = "ok" if db_status == "ok" else "degraded"
    return {
        "status": overall_status,
        "database": db_status,
        "redis": redis_status
    }
