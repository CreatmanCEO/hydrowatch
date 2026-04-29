"""Tests for well GeoJSON generation."""

import json

from data_generator.generate_wells import generate_wells_geojson


class TestWellGeneration:
    def test_generates_correct_count(self):
        geojson = generate_wells_geojson(n_wells=25)
        assert len(geojson["features"]) == 25

    def test_valid_geojson_structure(self):
        geojson = generate_wells_geojson(n_wells=5)
        assert geojson["type"] == "FeatureCollection"
        for f in geojson["features"]:
            assert f["type"] == "Feature"
            assert f["geometry"]["type"] == "Point"
            assert len(f["geometry"]["coordinates"]) == 2

    def test_coordinates_in_abu_dhabi_region(self):
        geojson = generate_wells_geojson(n_wells=10)
        for f in geojson["features"]:
            lon, lat = f["geometry"]["coordinates"]
            assert 54.0 < lon < 56.0, f"Longitude {lon} outside Abu Dhabi"
            assert 24.0 < lat < 25.0, f"Latitude {lat} outside Abu Dhabi"

    def test_realistic_well_properties(self):
        geojson = generate_wells_geojson(n_wells=10)
        for f in geojson["features"]:
            p = f["properties"]
            assert 20 < p["well_depth_m"] < 500
            assert 500 < p["last_tds_mgl"] < 15000
            assert 6.0 < p["last_ph"] < 9.5
            assert p["status"] in ("active", "inactive", "maintenance")
            assert "id" in p
            assert "cluster_id" in p

    def test_wells_grouped_in_clusters(self):
        geojson = generate_wells_geojson(n_wells=20, n_clusters=4)
        cluster_ids = {f["properties"]["cluster_id"] for f in geojson["features"]}
        assert len(cluster_ids) >= 3  # at least 3 clusters used

    def test_serializable_to_json(self):
        geojson = generate_wells_geojson(n_wells=5)
        json_str = json.dumps(geojson, ensure_ascii=False)
        assert len(json_str) > 100
