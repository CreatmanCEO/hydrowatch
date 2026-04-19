"""Seed database from generated GeoJSON and CSV files."""
import asyncio
import json
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.shape import from_shape
from shapely.geometry import shape

from models.database import Base, Well, Observation
from db.session import engine, async_session


async def seed_wells(session: AsyncSession, geojson_path: str):
    """Load wells from GeoJSON into database."""
    with open(geojson_path) as f:
        geojson = json.load(f)

    for feature in geojson["features"]:
        props = feature["properties"]
        geom = shape(feature["geometry"])

        well = Well(
            id=props["id"],
            name=props["name_en"],
            cluster_id=props["cluster_id"],
            cluster_name=props["cluster_name"],
            geometry=from_shape(geom, srid=4326),
            well_depth_m=props["well_depth_m"],
            aquifer_type=props["aquifer_type"],
            casing_diameter_mm=props["casing_diameter_mm"],
            ground_elevation_m=props["ground_elevation_m"],
            transmissivity_m2d=props["transmissivity_m2d"],
            storativity=props["storativity"],
            status=props["status"],
            current_yield_ls=props["current_yield_ls"],
            static_water_level_m=props["static_water_level_m"],
            last_tds_mgl=props["last_tds_mgl"],
            last_ph=props["last_ph"],
            last_chloride_mgl=props["last_chloride_mgl"],
            last_temperature_c=props["last_temperature_c"],
            operator=props["operator"],
            installation_date=props["installation_date"],
            properties=props,
        )
        session.add(well)

    await session.commit()
    print(f"Seeded {len(geojson['features'])} wells")


async def seed_observations(session: AsyncSession, csv_dir: str, well_ids: list[str]):
    """Load time series CSV files into database."""
    total = 0
    for well_id in well_ids:
        csv_path = Path(csv_dir) / f"{well_id}.csv"
        if not csv_path.exists():
            print(f"  Skipping {well_id} — no CSV found")
            continue

        df = pd.read_csv(csv_path, parse_dates=["timestamp"])

        observations = [
            Observation(
                well_id=row["well_id"],
                timestamp=row["timestamp"],
                debit_ls=row["debit_ls"],
                tds_mgl=row["tds_mgl"],
                ph=row["ph"],
                chloride_mgl=row["chloride_mgl"],
                water_level_m=row["water_level_m"],
                temperature_c=row["temperature_c"],
            )
            for _, row in df.iterrows()
        ]
        session.add_all(observations)
        total += len(observations)

    await session.commit()
    print(f"Seeded {total} observations for {len(well_ids)} wells")


async def create_tables():
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created")


async def main():
    """Full seed: create tables, load wells, load observations."""
    data_dir = Path(__file__).resolve().parent.parent.parent / "data"
    geojson_path = data_dir / "wells.geojson"
    obs_dir = data_dir / "observations"

    await create_tables()

    async with async_session() as session:
        await seed_wells(session, str(geojson_path))

        with open(geojson_path) as f:
            geojson = json.load(f)
        well_ids = [f["properties"]["id"] for f in geojson["features"]]

        if obs_dir.exists() and any(obs_dir.glob("*.csv")):
            await seed_observations(session, str(obs_dir), well_ids)
        else:
            print("No observation CSVs found, skipping observations seed")

    await engine.dispose()
    print("Seed complete!")


if __name__ == "__main__":
    asyncio.run(main())
