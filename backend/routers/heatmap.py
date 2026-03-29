from fastapi import APIRouter, Request
from models.schemas import HeatmapZone
from typing import List

router = APIRouter()

@router.get("/bengaluru", response_model=List[HeatmapZone])
async def get_heatmap_bengaluru():
    return [
        HeatmapZone(lat=12.9716, lng=77.5946, score=72, zone_type="freedom"),
        HeatmapZone(lat=12.9352, lng=77.6245, score=66, zone_type="freedom"),
        HeatmapZone(lat=12.9698, lng=77.7499, score=61, zone_type="freedom"),
        HeatmapZone(lat=12.9279, lng=77.6271, score=63, zone_type="freedom"),
        HeatmapZone(lat=12.9784, lng=77.6408, score=52, zone_type="freedom"),
        HeatmapZone(lat=12.9165, lng=77.6101, score=48, zone_type="freedom"),
        HeatmapZone(lat=12.9900, lng=77.5600, score=35, zone_type="constraint"),
        HeatmapZone(lat=13.0000, lng=77.5800, score=32, zone_type="constraint"),
        HeatmapZone(lat=12.9500, lng=77.5200, score=30, zone_type="constraint"),
        HeatmapZone(lat=13.0358, lng=77.5970, score=45, zone_type="constraint"),
    ]