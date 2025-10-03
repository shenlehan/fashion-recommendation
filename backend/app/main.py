from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import users, clothes, recommendation
from app.core.config import settings

app = FastAPI()

# CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this to restrict origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API routes
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(clothes.router, prefix="/api/clothes", tags=["clothes"])
app.include_router(recommendation.router, prefix="/api/recommendation", tags=["recommendation"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Fashion Recommendation API!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)