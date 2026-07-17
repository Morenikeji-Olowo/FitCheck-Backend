from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api.wardrobe import router as wardrobe_router
from shared.exceptions import FitCheckException
from core.config.settings import settings

app = FastAPI(title="FitCheck AI Service")

# Global exception handler — no try/except in routes
@app.exception_handler(FitCheckException)
async def fitcheck_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message
            }
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Something went wrong. Please try again."
            }
        }
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://10.0.2.2:3000"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(wardrobe_router, prefix="/api")

@app.get("/")
def health_check():
    return { "status": "FitCheck AI service is running" }