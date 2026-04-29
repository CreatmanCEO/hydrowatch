"""Tests for FastAPI main app endpoints."""
import json
import os
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

DATA_DIR = str(Path(__file__).resolve().parent.parent.parent / "data")
os.environ["DATA_DIR"] = DATA_DIR
# Set dummy API keys so config doesn't fail
os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("CEREBRAS_API_KEY", "test-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

from main import app

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestHealthEndpoint:

    async def test_health_ok(self, client):
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["wells_loaded"] > 0


class TestWellsEndpoint:

    async def test_get_wells_geojson(self, client):
        resp = await client.get("/api/wells")
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) > 0

    async def test_get_well_history(self, client):
        # Get first well ID
        wells_resp = await client.get("/api/wells")
        well_id = wells_resp.json()["features"][0]["properties"]["id"]

        resp = await client.get(f"/api/wells/{well_id}/history?parameter=debit_ls")
        assert resp.status_code == 200
        data = resp.json()
        assert data["well_id"] == well_id
        assert data["parameter"] == "debit_ls"
        assert len(data["timestamps"]) > 0

    async def test_get_well_history_404(self, client):
        resp = await client.get("/api/wells/NONEXISTENT-999/history")
        assert resp.status_code == 404


class TestCSVUpload:

    async def test_upload_valid_csv(self, client):
        # Use a real observation CSV
        obs_dir = Path(DATA_DIR) / "observations"
        csv_file = next(obs_dir.glob("*.csv"))

        with open(csv_file, "rb") as f:
            resp = await client.post(
                "/api/upload/csv",
                files={"file": (csv_file.name, f, "text/csv")},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "valid" in data
        assert "total_rows" in data

    async def test_upload_non_csv_rejected(self, client):
        resp = await client.post(
            "/api/upload/csv",
            files={"file": ("test.txt", b"hello", "text/plain")},
        )
        assert resp.status_code == 400


class TestChatStream:

    async def test_stream_returns_sse(self, client):
        resp = await client.post("/api/chat/stream", json={
            "message": "Show me all wells",
            "map_context": {
                "center_lat": 24.45,
                "center_lng": 54.65,
                "zoom": 10,
                "bbox": [54.0, 24.0, 56.0, 25.0],
            },
        })
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]

        # Parse SSE events
        events = []
        for line in resp.text.split("\n"):
            if line.startswith("data: ") and line != "data: [DONE]":
                events.append(json.loads(line[6:]))

        # Should have at least meta event
        assert len(events) >= 1
        assert events[0]["type"] == "meta"

    async def test_stream_with_selected_well(self, client):
        wells_resp = await client.get("/api/wells")
        well_id = wells_resp.json()["features"][0]["properties"]["id"]

        resp = await client.post("/api/chat/stream", json={
            "message": "What anomalies does this well have?",
            "map_context": {
                "center_lat": 24.45,
                "center_lng": 54.65,
                "zoom": 14,
                "bbox": [54.6, 24.4, 54.7, 24.5],
                "selected_well_id": well_id,
            },
        })
        assert resp.status_code == 200


class TestTaskClassifier:
    def test_classifies_interference(self):
        from main import _classify_task
        assert _classify_task("Check well interference patterns") == "interference_analysis"
        assert _classify_task("Wells competing for water") == "interference_analysis"
        assert _classify_task("Mutual influence between wells") == "interference_analysis"

    def test_classifies_drawdown(self):
        from main import _classify_task
        assert _classify_task("Show depression cone for well X") == "drawdown_analysis"
        assert _classify_task("What is the drawdown at this well?") == "drawdown_analysis"
        assert _classify_task("Generate isolines for AUH-01-001") == "drawdown_analysis"

    def test_classifies_water_quality(self):
        from main import _classify_task
        assert _classify_task("Generate a water quality report") == "water_quality_report"
        assert _classify_task("Check TDS levels in viewport") == "water_quality_report"

    def test_classifies_cluster_comparison(self):
        from main import _classify_task
        assert _classify_task("Compare clusters") == "cluster_comparison"
        assert _classify_task("Cross-cluster comparison") == "cluster_comparison"

    def test_classifies_daily_report(self):
        from main import _classify_task
        assert _classify_task("Generate daily report") == "daily_report"
        assert _classify_task("Daily monitoring summary") == "daily_report"
