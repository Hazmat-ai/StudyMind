from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, generate, studysets

app = FastAPI(title="StudyMind API", description="AI-powered study assistant API")

# Configure CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://studymind.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(generate.router, prefix="/generate", tags=["generate"])
app.include_router(studysets.router, prefix="/studysets", tags=["studysets"])

@app.get("/")
async def root():
    return {"message": "Welcome to the StudyMind API"}
