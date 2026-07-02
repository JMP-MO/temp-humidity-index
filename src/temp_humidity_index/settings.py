from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.yaml"
LOCAL_SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.local.yaml"


@dataclass(frozen=True)
class ProjectPaths:
    data_dir: Path
    download_dir: Path
    charts_dir: Path


@dataclass(frozen=True)
class ProjectFiles:
    raw_grib: str
    raw_nc: str
    wet_bulb_nc: str
    thi_nc: str


@dataclass(frozen=True)
class Settings:
    paths: ProjectPaths
    files: ProjectFiles

    @property
    def raw_grib_path(self) -> Path:
        return self.paths.download_dir / self.files.raw_grib

    @property
    def raw_nc_path(self) -> Path:
        return self.paths.data_dir / self.files.raw_nc

    @property
    def wet_bulb_nc_path(self) -> Path:
        return self.paths.data_dir / self.files.wet_bulb_nc

    @property
    def thi_nc_path(self) -> Path:
        return self.paths.data_dir / self.files.thi_nc


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        loaded = yaml.safe_load(f) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Settings file must contain a top-level mapping: {path}")
    return loaded


def _deep_update(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_update(base[key], value)
        else:
            base[key] = value
    return base


def _resolve_path(path_value: str) -> Path:
    p = Path(path_value)
    return p if p.is_absolute() else (PROJECT_ROOT / p)


def load_settings() -> Settings:
    settings_path = Path(os.getenv("THI_SETTINGS_FILE", str(DEFAULT_SETTINGS_PATH)))
    if not settings_path.exists():
        raise FileNotFoundError(f"Settings file not found: {settings_path}")

    data = _load_yaml(settings_path)
    if LOCAL_SETTINGS_PATH.exists():
        _deep_update(data, _load_yaml(LOCAL_SETTINGS_PATH))

    paths_data = data.get("paths", {})
    files_data = data.get("files", {})

    data_dir = _resolve_path(os.getenv("THI_DATA_DIR", paths_data.get("data_dir", ".")))
    download_dir = _resolve_path(
        os.getenv("THI_DOWNLOAD_DIR", paths_data.get("download_dir", str(data_dir)))
    )
    charts_dir = _resolve_path(os.getenv("THI_CHARTS_DIR", paths_data.get("charts_dir", "charts")))

    paths = ProjectPaths(
        data_dir=data_dir,
        download_dir=download_dir,
        charts_dir=charts_dir,
    )
    files = ProjectFiles(
        raw_grib=files_data.get("raw_grib", "ifs_2t_dp_msl.grib"),
        raw_nc=files_data.get("raw_nc", "ifs_2t_dp_msl.nc"),
        wet_bulb_nc=files_data.get("wet_bulb_nc", "ifs_2t_dp_msl_tw.nc"),
        thi_nc=files_data.get("thi_nc", "ifs_thi.nc"),
    )

    settings = Settings(paths=paths, files=files)

    settings.paths.data_dir.mkdir(parents=True, exist_ok=True)
    settings.paths.download_dir.mkdir(parents=True, exist_ok=True)
    settings.paths.charts_dir.mkdir(parents=True, exist_ok=True)

    return settings
