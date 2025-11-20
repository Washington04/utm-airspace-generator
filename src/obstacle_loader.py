#!/usr/bin/env python3
"""
Parse FAA Digital Obstacle File (fixed-width .dat) into a GeoJSON / GeoDataFrame.

OAS#   V CO ST CITY        LATITUDE ... LONGITUDE ... OBSTACLE ... AGL ...
53-000685 0 US WA VANCOUVER 45 34 03.80N 122 24 51.58W T-L TWR ...

Usage (from repo root):
  python src/obstacle_loader.py
"""

import re
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parent.parent
DOF_PATH = ROOT_DIR / "data" / "obstacles" / "faa_dof.dat"
OUTPUT_GEOJSON = ROOT_DIR / "data" / "obstacles" / "faa_dof_wa.geojson"

# Regex based on your screenshot:
LINE_RE = re.compile(
    r"""^
    (?P<oas>\S+)\s+                     # OAS#
    (?P<v>\S+)\s+                       # V
    (?P<co>\S+)\s+                      # CO (country)
    (?P<st>\S+)\s+                      # ST (state)
    (?P<city>.+?)\s+                    # CITY (lazy, up to latitude)
    (?P<lat_deg>\d{2,3})\s+
    (?P<lat_min>\d{2})\s+
    (?P<lat_sec>\d{2}\.\d{2})(?P<lat_hem>[NS])\s+
    (?P<lon_deg>\d{2,3})\s+
    (?P<lon_min>\d{2})\s+
    (?P<lon_sec>\d{2}\.\d{2})(?P<lon_hem>[EW])\s+
    (?P<obstacle_type>.+?)\s+           # e.g. T-L TWR, VERTICAL STRUCTURE
    (?P<agl_cat>\d)\s+                  # AGL category (1 digit)
    (?P<agl_ht>\d{5})\s+                # AGL height (ft)
    (?P<amsl_ht>\d{5})                  # AMSL height (ft)
    """,
    re.VERBOSE,
)


def dms_to_decimal(deg: int, minute: int, sec: float, hemisphere: str) -> float:
    val = deg + minute / 60.0 + sec / 3600.0
    if hemisphere in ("S", "W"):
        val *= -1.0
    return val


def parse_dof(path: Path) -> gpd.GeoDataFrame:
    if not path.exists():
        raise FileNotFoundError(f"DOF file not found: {path}")

    rows = []
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    # Skip header / separator lines – in your file that's first 4 lines
    for line in lines[4:]:
        line = line.rstrip("\n")
        if not line.strip():
            continue

        m = LINE_RE.match(line)
        if not m:
            # You can uncomment this to debug odd lines:
            # print("No match for line:", line)
            continue

        g = m.groupdict()

        lat = dms_to_decimal(
            int(g["lat_deg"]),
            int(g["lat_min"]),
            float(g["lat_sec"]),
            g["lat_hem"],
        )
        lon = dms_to_decimal(
            int(g["lon_deg"]),
            int(g["lon_min"]),
            float(g["lon_sec"]),
            g["lon_hem"],
        )

        rows.append(
            {
                "oas": g["oas"],
                "state": g["st"],
                "city": g["city"].strip(),
                "obstacle_type": g["obstacle_type"].strip(),
                "agl_ft": int(g["agl_ht"]),
                "amsl_ft": int(g["amsl_ht"]),
                "lat": lat,
                "lon": lon,
            }
        )

    if not rows:
        raise RuntimeError("Parsed 0 obstacles – regex probably needs adjustment.")

    df = pd.DataFrame(rows)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=[Point(xy) for xy in zip(df["lon"], df["lat"])],
        crs="EPSG:4326",
    )
    return gdf


def main() -> None:
    print(f"Parsing DOF from: {DOF_PATH}")
    gdf = parse_dof(DOF_PATH)
    print(f"Parsed {len(gdf)} obstacles")

    OUTPUT_GEOJSON.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(OUTPUT_GEOJSON, driver="GeoJSON")
    print(f"Wrote GeoJSON → {OUTPUT_GEOJSON}")


if __name__ == "__main__":
    main()
