from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import score, routes, heatmap
import json

app = FastAPI(title="Freedom Map API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

with open("data/city_graph.json", "r") as f:
    CITY_DATA = json.load(f)
    app.state.nodes = {n["node_id"]: n for n in CITY_DATA["nodes"]}
    app.state.routes = CITY_DATA["routes"]

app.include_router(score.router, prefix="/api/score", tags=["Mobility Score"])
app.include_router(routes.router, prefix="/api/routes", tags=["Route Recommendation"])
app.include_router(heatmap.router, prefix="/api/heatmap", tags=["Heatmap"])

@app.get("/")
def root():
    return {"status": "Freedom Map API running", "version": "1.0.0"}