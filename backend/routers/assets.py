from __future__ import annotations
import mimetypes
import os
import pathlib

from fastapi import APIRouter

router = APIRouter(prefix="/assets", tags=["assets"])

_ASSETS = pathlib.Path(os.environ.get("ASSETS_DIR", str(pathlib.Path(__file__).parent.parent.parent / "assets")))

_CATEGORY_LABELS = {
    "reglements": "Reglemente",
    "vorlagen":   "Vorlagen & Formulare",
    "logos":      "Logos",
}


@router.get("/files")
def list_asset_files():
    """Return a flat listing of all files in the assets directory."""
    if not _ASSETS.exists():
        return []

    result = []
    for path in sorted(_ASSETS.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(_ASSETS)
        parts = rel.parts
        category = parts[0] if len(parts) > 1 else ""
        category_label = _CATEGORY_LABELS.get(
            category, category.capitalize() if category else "Sonstiges"
        )
        url_path = "/".join(rel.parts)
        result.append({
            "name": path.name,
            "path": url_path,
            "url": f"/media/{url_path}",
            "category": category,
            "category_label": category_label,
            "size": path.stat().st_size,
            "mime": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        })
    return result
