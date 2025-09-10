from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

# Import route modules
from .routes.auth import router as auth_router
from .routes.data import router as data_router

# Create FastAPI app
app = FastAPI(
    title="Fi Money MCP Client API",
    description="FastAPI backend for Fi Money MCP financial data integration",
    version="1.0.0"
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1", tags=["Authentication"])
app.include_router(data_router, prefix="/api/v1", tags=["Data"])

# Health check endpoint
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "message": "Fi Money MCP Client API is operational",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "api_version": "1.0.0",
        "environment": os.getenv("MODE", "fastapi"),
        "endpoints": [
            "/api/v1/authenticate",
            "/api/v1/fetch-data",
            "/api/v1/status"
        ]
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error occurred",
            "detail": repr(exc)

        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )