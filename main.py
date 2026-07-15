from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.image import router as image_router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="FitCheck AI Service")

# Allow Node.js backend to talk to this service
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Routes
app.include_router(image_router, prefix="/ai")

@app.get("/")
def health_check():
    return { "status": "FitCheck AI service is running" }