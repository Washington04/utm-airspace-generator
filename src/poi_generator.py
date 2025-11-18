#!/usr/bin/env python

import argparse
import os
import random

import geopandas as gpd
import pandas as pd


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Generate Points of Interest (hub, merchant, customer) from a grid."
    )
    ap.add_argument(
        "--grid",
        type=str,
        required=True,
        help="Path to grid GeoJSON with at least cell_id, centroid_lat, centroid_lon.",
    )
    ap.add_argument(
        "--n-hubs",
        type=int,
        default=1,
        help="Number of hubs to create.",
    )
    ap.add_argument(
        "--n-merchants",
        type=int,
        default=10,
        help="Number of merchant locations (restaurants).",
    )
    ap.add_argument(
        "--n-customers",
        type=int,
        default=10,
        help="Number of customer dropoff locations.",
    )
    ap.add_argument(
        "--out",
        type=str,
        default="data/points_of_interest.csv",
        help="Output CSV path.",
    )
    return ap.parse_args()


def load_grid(path: str) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)
    required_cols = {"cell_id", "centroid_lat", "centroid_lon"}
    missing = required_cols - set(gdf.columns)
    if missing:
        raise ValueError(
            f"Grid {path} is missing required columns: {', '.join(sorted(missing))}"
        )
    return gdf[["cell_id", "centroid_lat", "centroid_lon", "geometry"]].copy()


def create_pois(
    gdf: gpd.GeoDataFrame,
    n_hubs: int,
    n_merchants: int,
    n_customers: int,
) -> pd.DataFrame:

    rng_hub = random.Random(42)
    rng_merchant = random.Random(43)
    rng_customer = random.Random(44)

    # --- hubs ---
    hub_indices = rng_hub.sample(range(len(gdf)), k=min(n_hubs, len(gdf)))
    hubs = gdf.iloc[hub_indices].copy()
    hubs["poi_type"] = "hub"
    hubs["poi_name"] = [f"hub_{i+1}" for i in range(len(hubs))]

    # --- merchants ---
    merchant_indices = rng_merchant.sample(
        range(len(gdf)), k=min(n_merchants, len(gdf))
    )
    merchants = gdf.iloc[merchant_indices].copy()
    merchants["poi_type"] = "merchant"
    merchants["poi_name"] = [f"merchant_{i+1}" for i in range(len(merchants))]

    # --- customers ---
    customer_indices = rng_customer.sample(
        range(len(gdf)), k=min(n_customers, len(gdf))
    )
    customers = gdf.iloc[customer_indices].copy()
    customers["poi_type"] = "customer"
    customers["poi_name"] = [f"customer_{i+1}" for i in range(len(customers))]

    # Combine
    all_pois = pd.concat([hubs, merchants, customers], ignore_index=True)

    # Stable POI IDs
    all_pois["poi_id"] = all_pois.index.map(lambda i: f"poi_{i:04d}")

    # Round centroid coordinates for cleaner output
    all_pois["centroid_lat"] = all_pois["centroid_lat"].round(3)
    all_pois["centroid_lon"] = all_pois["centroid_lon"].round(3)

    # Keep geometry so we can write GeoJSON later
    return all_pois[
        [
            "poi_id",
            "poi_type",
            "poi_name",
            "cell_id",
            "centroid_lat",
            "centroid_lon",
            "geometry",
        ]
    ].copy()


def main() -> None:
    print("poi_generator: starting")  # debug print so we know it runs

    args = parse_args()

    gdf = load_grid(args.grid)

    pois_df = create_pois(
        gdf=gdf,
        n_hubs=args.n_hubs,
        n_merchants=args.n_merchants,
        n_customers=args.n_customers,
    )

    out_path = args.out
    out_dir = out_path.rsplit("/", 1)[0] if "/" in out_path else "."
    os.makedirs(out_dir, exist_ok=True)

    # 1) Write CSV (drop geometry column)
    csv_df = pois_df.drop(columns=["geometry"])
    csv_df.to_csv(out_path, index=False)

    # 2) Write GeoJSON with point geometry
    poi_geo_path = out_path.replace(".csv", ".geojson")
    pois_gdf = gpd.GeoDataFrame(pois_df, geometry="geometry", crs=gdf.crs)
    pois_gdf.to_file(poi_geo_path, driver="GeoJSON")

    print(f"poi_generator: wrote {len(pois_df)} POIs → {out_path} and {poi_geo_path}")


if __name__ == "__main__":
    main()