import geopandas as gpd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
dof = gpd.read_file(ROOT / "data/obstacles/faa_dof_wa.geojson")
seattle = gpd.read_file(ROOT / "data/seattle_city_limits.geojson")

dof_seattle = gpd.clip(dof, seattle.to_crs(dof.crs))
dof_seattle.to_file(ROOT / "data/obstacles/faa_dof_seattle.geojson",
                    driver="GeoJSON")
