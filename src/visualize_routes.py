#!/usr/bin/env python3
"""
Visualize flight routes from generated flights JSON on a Leaflet/Folium map.

Usage (from repo root):

  python src/visualize_routes.py
  python src/visualize_routes.py --flights output/flights_20251119_153045.json

Outputs an HTML map:

  output/flights_map_YYYYMMDD_HHMMSS.html
"""

import argparse
import json
import glob
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import geopandas as gpd


import folium


# ---- Paths based on your repo layout ----

SRC_DIR = Path(__file__).resolve().parent
ROOT_DIR = SRC_DIR.parent

OUTPUT_DIR = ROOT_DIR / "output"
DATA_DIR = ROOT_DIR / "data"
OBSTACLE_FILE = DATA_DIR / "obstacles" / "faa_dof_seattle.geojson"
CITY_LIMITS_FILE = DATA_DIR / "seattle_city_limits.geojson"
GRID_LATEST = OUTPUT_DIR / "output_latest.geojson"



def find_latest_flights_file() -> Optional[Path]:
    pattern = str(OUTPUT_DIR / "flights_*.json")
    matches = glob.glob(pattern)
    if not matches:
        return None
    # Sort by filename (timestamp in name) and take latest
    matches.sort()
    return Path(matches[-1])


def find_latest_grid_file() -> Optional[Path]:
    """Return output_latest.geojson if present, else latest grid_*.geojson."""
    if GRID_LATEST.exists():
        return GRID_LATEST

    pattern = str(OUTPUT_DIR / "grid_*.geojson")
    matches = glob.glob(pattern)
    if not matches:
        return None
    matches.sort()
    return Path(matches[-1])


def load_flights(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def compute_map_center(flights: Dict) -> List[float]:
    lats = []
    lons = []

    for f in flights.get("flights", []):
        for key in ("origin_poi", "destination_poi", "recovery_poi"):
            poi = f.get(key)
            if not poi:
                continue
            lat = poi.get("centroid_lat")
            lon = poi.get("centroid_lon")
            if lat is not None and lon is not None:
                lats.append(float(lat))
                lons.append(float(lon))

    if not lats or not lons:
        # Default to Seattle-ish
        return [47.6062, -122.3321]

    return [sum(lats) / len(lats), sum(lons) / len(lons)]


def add_city_limits_layer(m: folium.Map) -> None:
    if CITY_LIMITS_FILE.exists():
        folium.GeoJson(
            data=str(CITY_LIMITS_FILE),
            name="Seattle city limits",
        ).add_to(m)


def add_flight_routes_layer(m: folium.Map, flights: Dict) -> None:
    for f in flights.get("flights", []):
        origin = f.get("origin_poi") or {}
        dest = f.get("destination_poi") or {}
        hub = f.get("recovery_poi") or {}

        try:
            o_lat = float(origin["centroid_lat"])
            o_lon = float(origin["centroid_lon"])
            d_lat = float(dest["centroid_lat"])
            d_lon = float(dest["centroid_lon"])
            h_lat = float(hub["centroid_lat"])
            h_lon = float(hub["centroid_lon"])
        except (KeyError, TypeError, ValueError):
            # Skip flights with incomplete coordinates
            continue

        # Route: hub -> merchant -> customer -> hub
        points = [
            [h_lat, h_lon],
            [o_lat, o_lon],
            [d_lat, d_lon],
            [h_lat, h_lon],
        ]

        tooltip = f.get("flight_id", "flight")

        folium.PolyLine(
            locations=points,
            weight=2,
            opacity=0.7,
            tooltip=tooltip,
        ).add_to(m)


def add_obstacles_layer(m: folium.Map) -> None:
    if not OBSTACLE_FILE.exists():
        return

    gdf = gpd.read_file(OBSTACLE_FILE)

    # Option 1: simple points as small markers
    for _, row in gdf.iterrows():
        lat = row["lat"]
        lon = row["lon"]
        agl = row.get("agl_ft", None)
        obs_type = row.get("obstacle_type", "")

        tooltip = f"{obs_type} ({agl} ft AGL)" if agl is not None else obs_type

        folium.CircleMarker(
            location=[lat, lon],
            radius=4,
            opacity=0.7,
            fill=True,
            fill_opacity=0.7,
            tooltip=tooltip,
        ).add_to(m)


def build_map(flights: Dict) -> folium.Map:
    center = compute_map_center(flights)
    m = folium.Map(location=center, zoom_start=12)

    add_city_limits_layer(m)
    add_obstacles_layer(m)       
    add_flight_routes_layer(m, flights)

    folium.LayerControl().add_to(m)
    return m



def save_map(m: folium.Map) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = OUTPUT_DIR / f"flights_map_{ts}.html"
    m.save(str(out_path))
    return out_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Visualize UTM flight routes on a Folium map."
    )
    parser.add_argument(
        "--flights",
        type=str,
        default=None,
        help="Path to flights JSON (default: latest output/flights_*.json)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.flights:
        flights_path = Path(args.flights)
    else:
        flights_path = find_latest_flights_file()
        if flights_path is None:
            raise SystemExit(
                "No flights_*.json found in output/. "
                "Run flight_generator.py first."
            )

    if not flights_path.exists():
        raise SystemExit(f"Flights file not found: {flights_path}")

    flights = load_flights(flights_path)
    m = build_map(flights)
    out_path = save_map(m)

    print(f"Map written to: {out_path}")
    print("Open this file in your browser to view flight routes.")


if __name__ == "__main__":
    main()
