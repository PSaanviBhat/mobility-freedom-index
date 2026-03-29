from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize data layer instantly on startup
import services.data_layer 

# Import API endpoints from the routers folder
from routers import routes, score, heatmap

app = FastAPI(title="FreedomMap API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(routes.router)

# Assuming score and heatmap don't have prefixes defined inside them yet:
app.include_router(score.router, prefix="/api/v1/score", tags=["Mobility Score"])
app.include_router(heatmap.router, prefix="/api/v1/heatmap", tags=["Heatmap"])

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "FreedomMap API running", 
        "version": "1.0.0",
        "graph_nodes_loaded": len(services.data_layer.CITY_GRAPH.nodes) 
    }