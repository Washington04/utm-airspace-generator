"""
Drone Flight Grid Generator (Boundary-only version)

- Input:
    * --boundary: path to a boundary polygon (e.g., city limits, GeoJSON)
    * --cell: grid cell size in meters

- Process:
    1) Load boundary
    2) Compute bounding box around boundary
    3) Build rectangular grid over the bounding box (in UTM)
    4) Reproject grid to EPSG:4326
    5) Clip grid to the boundary shape
    6) Write GeoJSON

Example:
    python grid_generator.py \
        --boundary data/seattle_boundary.geojson \
        --cell 100 \
        --out output/grid_seattle_100m.geojson
"""

import argparse
import math
import os
import logging

import geopandas as gpd
from shapely.geometry import box

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("grid_generator")


def _utm_epsg_for_latlon(lat: float, lon: float) -> str:
    """
    Pick a local UTM CRS for good meter-based tiling.
    """
    zone = int(math.floor((lon + 180) / 6) + 1)
    if lat >= 0:
        return f"EPSG:{32600 + zone}"  # WGS84 / UTM zone N
    else:
        return f"EPSG:{32700 + zone}"  # WGS84 / UTM zone S


def bounds_from_boundary(boundary_path: str):
    """
    Load boundary file and return (minx, miny, maxx, maxy) in EPSG:4326.
    """
    boundary = gpd.read_file(boundary_path)
    if boundary.crs is None:
        boundary = boundary.set_crs("EPSG:4326")
    else:
        boundary = boundary.to_crs("EPSG:4326")

    minx, miny, maxx, maxy = boundary.total_bounds
    log.info("Boundary bounds (lon/lat): west=%s south=%s east=%s north=%s", minx, miny, maxx, maxy)
    return minx, miny, maxx, maxy, boundary


def build_grid_from_bounds(north: float, south: float, west: float, east: float, cell_m: float) -> gpd.GeoDataFrame:
    """
    Build a rectangular grid over the given lat/lon bounding box.
    """
    if not (south < north and west < east):
        raise ValueError("Invalid bounds: ensure south < north and west < east.")
    if cell_m <= 0:
        raise ValueError("Cell size (meters) must be > 0.")

    log.info(
        "Building grid: north=%s south=%s west=%s east=%s cell=%sm",
        north,
        south,
        west,
        east,
        cell_m,
    )

    # Bounding box in geographic CRS
    bounds_gdf = gpd.GeoDataFrame(geometry=[box(west, south, east, north)], crs="EPSG:4326")

    # Choose a UTM CRS around the bbox center for meter-accurate gridding
    centroid = bounds_gdf.geometry.iloc[0].centroid
    utm_epsg = _utm_epsg_for_latlon(lat=centroid.y, lon=centroid.x)
    log.info("Using UTM CRS: %s", utm_epsg)

    # Reproject bounds to UTM (meters)
    bounds_utm = bounds_gdf.to_crs(utm_epsg)
    minx, miny, maxx, maxy = bounds_utm.total_bounds

    cells = []
    y = miny
    while y < maxy:
        x = minx
        while x < maxx:
            x2 = min(x + cell_m, maxx)
            y2 = min(y + cell_m, maxy)
            if (x2 - x) > 0 and (y2 - y) > 0:
                cells.append(box(x, y, x2, y2))
            x += cell_m
        y += cell_m

    gdf_utm = gpd.GeoDataFrame(
        {"cell_id": list(range(1, len(cells) + 1))},
        geometry=cells,
        crs=utm_epsg,
    )

    # Back to EPSG:4326 for universal GeoJSON output
    gdf_wgs84 = gdf_utm.to_crs("EPSG:4326")
    return gdf_wgs84


def clip_to_boundary(grid_gdf: gpd.GeoDataFrame, boundary_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Clip grid cells to a boundary polygon (e.g., city limits).
    """
    log.info("Clipping grid to boundary shape...")
    # Ensure CRS match
    boundary_gdf = boundary_gdf.to_crs(grid_gdf.crs)
    clipped = gpd.overlay(grid_gdf, boundary_gdf, how="intersection")
    clipped = clipped.reset_index(drop=True)
    clipped["cell_id"] = clipped.index + 1
    log.info("Clipped grid has %s cells", len(clipped))
    return clipped


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Generate a grid clipped to a boundary polygon.")
    ap.add_argument(
        "--boundary",
        type=str,
        required=True,
        help="Boundary file path (GeoJSON/SHP), e.g., data/seattle_boundary.geojson",
    )
    ap.add_argument(
        "--cell",
        type=float,
        required=True,
        help="Cell size in meters (e.g., 100, 250, 1000)",
    )
    ap.add_argument(
        "--out",
        type=str,
        default="output/grid.geojson",
        help="Output GeoJSON path",
    )
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    # 1) Load boundary and compute bounding box
    minx, miny, maxx, maxy, boundary = bounds_from_boundary(args.boundary)

    # 2) Build rectangular grid over that bounding box
    gdf = build_grid_from_bounds(
        north=maxy,
        south=miny,
        west=minx,
        east=maxx,
        cell_m=args.cell,
    )

    # 3) Clip grid to the boundary
    gdf = clip_to_boundary(gdf, boundary)

    # 4) Write output
    try:
        gdf.to_file(args.out, driver="GeoJSON")
    except Exception:
        log.warning("GeoJSON driver failed; falling back to writing raw GeoJSON text.")
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(gdf.to_json())

    log.info("Finished. Wrote %s cells to %s", len(gdf), args.out)


if __name__ == "__main__":
    main()
