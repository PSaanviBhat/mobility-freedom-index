from fastapi import FastAPI
from routers import score

app = FastAPI()

app.include_router(score.router, prefix="/api/score")

@app.get("/")
def root():
    return {"status": "works"}