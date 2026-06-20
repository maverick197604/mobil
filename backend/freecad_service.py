"""
FreeCAD Python API wrapper for CAD file conversion.
Attempts to use FreeCAD Python API; falls back gracefully if not installed.
"""

import os
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def convert_to_stl(input_path: str, output_path: str) -> dict:
    """
    Convert a CAD file to STL format.

    Supports: .fcstd, .step, .stp, .iges, .igs, .stl

    Returns a dict with keys:
        success (bool), message (str), output_path (str or None)
    """
    input_path = str(input_path)
    output_path = str(output_path)
    suffix = Path(input_path).suffix.lower()

    # STL files need no conversion — just copy
    if suffix == ".stl":
        shutil.copy2(input_path, output_path)
        return {
            "success": True,
            "message": "STL-Datei direkt kopiert.",
            "output_path": output_path,
        }

    # Try to use FreeCAD Python API
    freecad_available = _try_import_freecad()

    if not freecad_available:
        return {
            "success": False,
            "message": (
                "FreeCAD ist nicht installiert. Bitte FreeCAD installieren, um "
                "STEP-, IGES- und FCStd-Dateien zu konvertieren. "
                "Unter Ubuntu/Debian: sudo apt install freecad. "
                "STL-Dateien können ohne FreeCAD angezeigt werden."
            ),
            "output_path": None,
        }

    try:
        if suffix == ".fcstd":
            return _convert_fcstd(input_path, output_path)
        elif suffix in (".step", ".stp", ".iges", ".igs"):
            return _convert_step_iges(input_path, output_path)
        else:
            return {
                "success": False,
                "message": f"Nicht unterstütztes Dateiformat: {suffix}",
                "output_path": None,
            }
    except Exception as exc:
        logger.exception("Fehler bei der Konvertierung: %s", exc)
        return {
            "success": False,
            "message": f"Konvertierungsfehler: {exc}",
            "output_path": None,
        }


def _try_import_freecad() -> bool:
    """Attempt to import FreeCAD; return True if successful."""
    import sys

    candidates = [
        "/usr/lib/freecad/lib",
        "/usr/lib/freecad-python3/lib",
        "/usr/lib/freecad/lib64",
        "/usr/local/lib/freecad/lib",
        "/opt/freecad/lib",
    ]
    for path in candidates:
        if path not in sys.path and os.path.isdir(path):
            sys.path.insert(0, path)

    try:
        import FreeCAD  # noqa: F401
        return True
    except ImportError:
        return False


def _convert_fcstd(input_path: str, output_path: str) -> dict:
    """Convert a FreeCAD .fcstd file to STL."""
    import FreeCAD
    import Mesh  # FreeCAD mesh module

    doc = FreeCAD.open(input_path)
    shapes = []

    for obj in doc.Objects:
        if hasattr(obj, "Shape") and obj.Shape is not None:
            try:
                mesh = obj.Shape.tessellate(0.1)
                shapes.append(mesh)
            except Exception as e:
                logger.warning("Objekt %s konnte nicht tesselliert werden: %s", obj.Name, e)

    if not shapes:
        FreeCAD.closeDocument(doc.Name)
        return {
            "success": False,
            "message": "Keine exportierbaren Formen in der FCStd-Datei gefunden.",
            "output_path": None,
        }

    # Build a combined mesh and export
    combined = Mesh.Mesh()
    for obj in doc.Objects:
        if hasattr(obj, "Shape") and obj.Shape is not None:
            try:
                m = Mesh.Mesh(obj.Shape.tessellate(0.1))
                combined.addMesh(m)
            except Exception:
                pass

    FreeCAD.closeDocument(doc.Name)
    combined.write(output_path)

    return {
        "success": True,
        "message": "FCStd-Datei erfolgreich in STL konvertiert.",
        "output_path": output_path,
    }


def _convert_step_iges(input_path: str, output_path: str) -> dict:
    """Convert STEP or IGES file to STL using FreeCAD Part module."""
    import Part

    shape = Part.read(input_path)
    if shape is None or shape.isNull():
        return {
            "success": False,
            "message": "Die CAD-Datei konnte nicht gelesen werden oder ist leer.",
            "output_path": None,
        }

    shape.exportStl(output_path)

    return {
        "success": True,
        "message": "STEP/IGES-Datei erfolgreich in STL konvertiert.",
        "output_path": output_path,
    }
