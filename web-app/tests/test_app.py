"""Unit tests for the Flask web application."""

# pylint: disable=redefined-outer-name, import-error
import pytest
from bson.objectid import ObjectId
from app import create_app


@pytest.fixture
def client():
    """
    Create and yield Flask app
    """
    app = create_app()
    app.testing = True  # necessary for assertions to work correctly
    with app.test_client() as client:
        yield client


def test_home_page_loads(client):
    """GET / returns 200"""
    response = client.get("/")
    assert response.status_code == 200


def test_filter_by_emotion(client):
    """GET /?emotion=happy returns 200 and contains happy"""
    response = client.get("/?emotion=happy")
    assert response.status_code == 200
    assert b"happy" in response.data.lower()


def test_filter_no_results(client):
    """GET /?emotion=fearful returns 200 even with no matching scans"""
    response = client.get("/?emotion=fearful")
    assert response.status_code == 200


def test_home_page_dummy_data(client):
    """Force the app to use dummy data by setting the DB connection to None"""
    client.application.db = None
    response = client.get("/")
    assert response.status_code == 200
    assert b"surprise" in response.data.lower()


def test_practice_page_loads(client):
    """GET /practice returns 200"""
    response = client.get("/practice")
    assert response.status_code == 200


def test_dummy_data_with_filter(client):
    """Test that the dummy data block correctly filters by emotion"""
    client.application.db = None
    response = client.get("/?emotion=sad")
    assert response.status_code == 200
    assert b"sad" in response.data.lower()


def test_debug_route_no_db(client):
    """GET /debug returns an error JSON when the DB is not connected"""
    client.application.db = None
    response = client.get("/debug")
    assert response.status_code == 200
    assert b"error" in response.data.lower()


def test_home_page_with_db_data(client):
    """Test the database loops by inserting a dummy scan"""
    if client.application.db is not None:
        collection = client.application.db[client.application.collection_name]
        collection.insert_one(
            {
                "status": "done",
                "predicted_emotion": "happy",
                "target_emotion": "happy",
                "match_score": 0.95,
                "passed": True,
                "created_at": "2026-04-18 10:00:00",
            }
        )
        response = client.get("/")
        assert response.status_code == 200
        assert b"happy" in response.data.lower()
        collection.delete_many({})


def test_home_page_db_filter_logic(client):
    """Test the emotion_filter logic when the DB is connected"""
    if client.application.db is not None:
        collection = client.application.db[client.application.collection_name]
        collection.insert_one(
            {
                "status": "done",
                "predicted_emotion": "fear",
                "created_at": "2026-04-18 10:00:00",
            }
        )
        response = client.get("/?emotion=fear")
        assert response.status_code == 200
        assert b"fear" in response.data.lower()

        collection.delete_many({})


def test_practice_submit_missing_data(client):
    """Test missing data in /practice/submit returns 400"""
    response = client.post("/practice/submit", json={"target_emotion": "happy"})
    assert response.status_code == 400
    assert b"missing image data" in response.data.lower()


def test_practice_submit_exception(client):
    """Test malformed image data triggers 500 exception"""
    response = client.post(
        "/practice/submit",
        json={"image_data": "invalid_data_without_comma", "target_emotion": "happy"},
    )
    assert response.status_code == 500


def test_practice_submit_success(client):
    """Test a successful valid submission"""
    if client.application.db is not None:
        response = client.post(
            "/practice/submit",
            json={
                "image_data": "data:image/jpeg;base64,ZmFrZWRhdGE=",
                "target_emotion": "happy",
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "scan_id" in data

        collection = client.application.db[client.application.collection_name]
        collection.delete_one({"_id": ObjectId(data["scan_id"])})


def test_practice_result_no_db(client):
    """Test /practice/result without DB connection returns 500"""
    client.application.db = None
    response = client.get("/practice/result/507f1f77bcf86cd799439011")
    assert response.status_code == 500


def test_practice_result_invalid_id(client):
    """Test an invalid ObjectId format triggers 500 exception"""
    if client.application.db is not None:
        response = client.get("/practice/result/invalid_id")
        assert response.status_code == 500


def test_practice_result_found_and_not_found(client):
    """Test finding and failing to find specific scan_ids"""
    if client.application.db is not None:
        collection = client.application.db[client.application.collection_name]

        response_not_found = client.get("/practice/result/507f1f77bcf86cd799439011")
        assert response_not_found.status_code == 404

        inserted = collection.insert_one({"status": "done", "target_emotion": "sad"})
        scan_id = str(inserted.inserted_id)

        response_found = client.get(f"/practice/result/{scan_id}")
        assert response_found.status_code == 200
        assert response_found.get_json()["target_emotion"] == "sad"

        collection.delete_one({"_id": inserted.inserted_id})
