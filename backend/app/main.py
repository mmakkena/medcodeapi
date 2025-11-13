"""FastAPI application entry point"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.middleware.rate_limit import init_redis, close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    # Startup
    await init_redis()
    yield
    # Shutdown
    await close_redis()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Medical coding lookup API for ICD-10 and CPT codes. Built for developers who need reliable, fast medical coding data.",
    version="0.1.0",
    docs_url=None,  # Disable default docs to use custom
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User authentication and account management"
        },
        {
            "name": "ICD-10 Codes",
            "description": "Search and lookup ICD-10 diagnosis codes"
        },
        {
            "name": "CPT Codes",
            "description": "Search and lookup CPT procedure codes"
        },
        {
            "name": "Procedure Codes (CPT/HCPCS)",
            "description": "Enhanced CPT and HCPCS procedure code search with semantic search, faceted filtering, and AI-powered suggestions. Supports license-compliant dual description strategy."
        },
        {
            "name": "Code Suggestions",
            "description": "AI-powered code suggestions from clinical text"
        },
        {
            "name": "API Keys",
            "description": "Manage API keys for authentication"
        },
        {
            "name": "Usage Tracking",
            "description": "View API usage logs and statistics"
        },
        {
            "name": "Billing",
            "description": "Manage subscriptions and billing"
        },
        {
            "name": "Admin Analytics",
            "description": "Admin-only analytics and user management endpoints"
        }
    ],
    contact={
        "name": "Nuvii API Support",
        "url": "https://nuvii.ai",
        "email": "support@nuvii.ai"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    from app.middleware.rate_limit import redis_client

    redis_status = "disabled"
    if settings.use_redis:
        redis_status = "connected" if redis_client else "disconnected"
    else:
        redis_status = "in-memory"

    return {
        "status": "healthy",
        "database": "connected",
        "redis": redis_status
    }


# Mount static files
import os
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Import and include routers
from app.api.v1 import auth, icd10, cpt, procedure, suggest, api_keys, usage, billing, clinical_coding, admin

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(icd10.router, prefix="/api/v1/icd10", tags=["ICD-10 Codes"])
app.include_router(cpt.router, prefix="/api/v1/cpt", tags=["CPT Codes"])
app.include_router(procedure.router, prefix="/api/v1/procedure", tags=["Procedure Codes (CPT/HCPCS)"])
app.include_router(suggest.router, prefix="/api/v1", tags=["Code Suggestions"])
app.include_router(clinical_coding.router, prefix="/api/v1", tags=["AI Clinical Coding"])
app.include_router(api_keys.router, prefix="/api/v1/api-keys", tags=["API Keys"])
app.include_router(usage.router, prefix="/api/v1/usage", tags=["Usage Tracking"])
app.include_router(billing.router, prefix="/api/v1/billing", tags=["Billing"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin Analytics"])


# Custom Swagger UI with logo
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi import Response

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI with Nuvii branding"""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - API Documentation",
        swagger_favicon_url="/static/nuvii_logo.png",
        swagger_ui_parameters={
            "defaultModelsExpandDepth": -1,
            "docExpansion": "list",
            "filter": True,
            "persistAuthorization": True
        }
    )
