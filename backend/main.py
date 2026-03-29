from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import services.data_layer
from routers import routes, score, heatmap

app = FastAPI(title="FreedomMap API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Keep all APIs versioned under /api/v1
app.include_router(score.router, prefix="/api/v1/score", tags=["Mobility Score"])
app.include_router(routes.router)  # routes.py already has /api/v1/routes prefix
app.include_router(heatmap.router, prefix="/api/v1/heatmap", tags=["Heatmap"])

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "FreedomMap API running",
        "version": "1.0.0",
        "graph_nodes_loaded": services.data_layer.CITY_GRAPH.number_of_nodes(),
    }