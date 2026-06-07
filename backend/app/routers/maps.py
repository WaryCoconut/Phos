import json
import os
import re
import uuid

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse

router = APIRouter(prefix="/maps", tags=["maps"])
MAPS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "custom_maps")


def _ensure_dir():
    os.makedirs(MAPS_DIR, exist_ok=True)


def _safe_map_path(map_id: str) -> str:
    # Validate UUID format to prevent path traversal
    if not re.fullmatch(r"[0-9a-f\-]{36}", map_id):
        raise HTTPException(status_code=400, detail="Identifiant de carte invalide")
    return os.path.join(MAPS_DIR, f"{map_id}.json")


@router.post("/upload")
async def upload_map(file: UploadFile = File(...)):
    _ensure_dir()
    content = await file.read()
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=400, detail="Fichier GeoJSON invalide (JSON mal formé)")

    geo_type = data.get("type")
    if geo_type not in ("FeatureCollection", "Feature"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un GeoJSON FeatureCollection")

    # Basic size guard: 50 MB max
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Fichier trop volumineux (max 50 Mo)")

    map_id = str(uuid.uuid4())
    path = _safe_map_path(map_id)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.decode("utf-8"))

    # Detect available properties from first feature
    features = data.get("features", []) if geo_type == "FeatureCollection" else [data]
    available_props: list[str] = []
    if features:
        first_props = features[0].get("properties") or {}
        available_props = list(first_props.keys())
        # Also include feature-level id if present
        if features[0].get("id") is not None and "id" not in available_props:
            available_props = ["_feature_id"] + available_props

    return {
        "map_id": map_id,
        "feature_count": len(features),
        "available_properties": available_props,
    }


@router.get("/{map_id}")
async def get_map(map_id: str):
    path = _safe_map_path(map_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Carte introuvable")
    return FileResponse(path, media_type="application/json")


@router.delete("/{map_id}")
async def delete_map(map_id: str):
    path = _safe_map_path(map_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Carte introuvable")
    os.remove(path)
    return {"message": "Carte supprimée"}
