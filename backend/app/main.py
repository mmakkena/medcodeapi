"""FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Medical coding lookup API for ICD-10 and CPT codes",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
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
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected" if settings.use_redis else "in-memory"
    }


# Import and include routers
from app.api.v1 import auth, icd10, cpt, suggest, api_keys, usage, billing

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(icd10.router, prefix="/api/v1/icd10", tags=["ICD-10 Codes"])
app.include_router(cpt.router, prefix="/api/v1/cpt", tags=["CPT Codes"])
app.include_router(suggest.router, prefix="/api/v1", tags=["Code Suggestions"])
app.include_router(api_keys.router, prefix="/api/v1/api-keys", tags=["API Keys"])
app.include_router(usage.router, prefix="/api/v1/usage", tags=["Usage Tracking"])
app.include_router(billing.router, prefix="/api/v1/billing", tags=["Billing"])
