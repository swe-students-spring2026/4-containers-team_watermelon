"""Unit tests for the Flask web application."""

# pylint: disable=redefined-outer-name
import base64
from unittest.mock import MagicMock, patch

import pytest
from bson import ObjectId

from app import _build_scan_doc, _save_image, create_app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def app_no_db():
    """App with no DB connection (simulates CI / offline environment)."""
    flask_app = create_app()
    flask_app.testing = True
    flask_app.db = None
    return flask_app


@pytest.fixture
def client_no_db(app_no_db):
    """Test client with no DB."""
    with app_no_db.test_client() as client:
        yield client


@pytest.fixture
def mock_collection():
    """A mock pymongo collection."""
    return MagicMock()


@pytest.fixture
def app_with_db(mock_collection):
    """App with a mocked DB."""
    flask_app = create_app()
    flask_app.testing = True
    flask_app.db = MagicMock()
    flask_app.db.__getitem__.return_value = mock_collection
    flask_app.collection_name = "scans"
    return flask_app


@pytest.fixture
def client_with_db(app_with_db):
    """Test client with a mocked DB."""
    with app_with_db.test_client() as client:
        yield client


# ---------------------------------------------------------------------------
# Home / dashboard
# ---------------------------------------------------------------------------


def test_home_page_loads(client_no_db):
    """GET / returns 200 without a DB."""
    response = client_no_db.get("/")
    assert response.status_code == 200


def test_home_filter_by_emotion(client_no_db):
    """GET /?emotion=happy returns 200 and contains the word."""
    response = client_no_db.get("/?emotion=happy")
    assert response.status_code == 200
    assert b"happy" in response.data.lower()


def test_home_filter_unknown_emotion(client_no_db):
    """GET /?emotion=unknown returns 200 even with no matching data."""
    response = client_no_db.get("/?emotion=unknown")
    assert response.status_code == 200


def test_home_with_db_all_filter(client_with_db, mock_collection):
    """GET / with DB connected, no filter."""
    scan = {
        "_id": ObjectId(),
        "status": "done",
        "predicted_emotion": "happy",
        "target_emotion": "happy",
        "match_score": 0.9,
        "passed": True,
        "created_at": None,
        "processed_at": None,
    }
    mock_collection.find.return_value.sort.return_value.limit.return_value = [scan]
    mock_collection.find.return_value.__iter__ = lambda _: iter([scan])
    response = client_with_db.get("/")
    assert response.status_code == 200


def test_home_with_db_emotion_filter(client_with_db, mock_collection):
    """GET /?emotion=sad with DB connected uses predicted_emotion filter."""
    mock_collection.find.return_value.sort.return_value.limit.return_value = []
    mock_collection.find.return_value.__iter__ = lambda _: iter([])
    response = client_with_db.get("/?emotion=sad")
    assert response.status_code == 200


def test_home_emotion_counts(client_with_db, mock_collection):
    """Emotion counts are incremented for known predicted emotions."""
    scan = {
        "_id": ObjectId(),
        "status": "done",
        "predicted_emotion": "fear",
        "target_emotion": "fear",
        "match_score": 0.5,
        "passed": False,
        "created_at": None,
        "processed_at": None,
    }

    call_count = [0]

    def fake_find(_query=None):
        call_count[0] += 1
        mock = MagicMock()
        if call_count[0] == 1:
            mock.sort.return_value.limit.return_value = [scan]
        else:
            mock.__iter__ = lambda s: iter([scan])
        return mock

    mock_collection.find.side_effect = fake_find
    response = client_with_db.get("/")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Debug route
# ---------------------------------------------------------------------------


def test_debug_no_db(client_no_db):
    """GET /debug returns error JSON when DB is None."""
    response = client_no_db.get("/debug")
    assert response.status_code == 200
    assert b"error" in response.data.lower()


def test_debug_with_db(client_with_db):
    """GET /debug returns scan list when DB is connected."""
    client_with_db.application.db = MagicMock()
    scan = {"_id": ObjectId(), "status": "done"}
    client_with_db.application.db.__getitem__.return_value.find.return_value = [scan]
    response = client_with_db.get("/debug")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Practice screen
# ---------------------------------------------------------------------------


def test_practice_page_loads(client_no_db):
    """GET /practice returns 200."""
    response = client_no_db.get("/practice")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# /practice/submit
# ---------------------------------------------------------------------------


def test_practice_submit_no_db(client_no_db):
    """POST /practice/submit returns 500 when DB is None."""
    response = client_no_db.post(
        "/practice/submit",
        json={
            "image_data": "data:image/jpeg;base64,ZmFrZQ==",
            "target_emotion": "happy",
        },
    )
    assert response.status_code == 500
    assert b"No database connection" in response.data


def test_practice_submit_missing_image(client_with_db):
    """POST /practice/submit with no image_data returns 400."""
    response = client_with_db.post("/practice/submit", json={"target_emotion": "happy"})
    assert response.status_code == 400
    assert b"missing" in response.data.lower()


def test_practice_submit_missing_emotion(client_with_db):
    """POST /practice/submit with no target_emotion returns 400."""
    response = client_with_db.post(
        "/practice/submit",
        json={"image_data": "data:image/jpeg;base64,ZmFrZQ=="},
    )
    assert response.status_code == 400


def test_practice_submit_invalid_image(client_with_db):
    """POST /practice/submit with malformed image_data returns 500."""
    response = client_with_db.post(
        "/practice/submit",
        json={"image_data": "no_comma_here", "target_emotion": "happy"},
    )
    assert response.status_code == 500


def test_practice_submit_success(client_with_db, mock_collection, tmp_path):
    """POST /practice/submit with valid data returns scan_id."""
    fake_id = ObjectId()
    mock_collection.insert_one.return_value = MagicMock(inserted_id=fake_id)

    image_bytes = base64.b64encode(b"fake_image_data").decode()
    image_data = f"data:image/jpeg;base64,{image_bytes}"

    with patch("app._save_image") as mock_save:
        mock_save.return_value = tmp_path / "test.jpg"
        (tmp_path / "test.jpg").write_bytes(b"fake")
        response = client_with_db.post(
            "/practice/submit",
            json={"image_data": image_data, "target_emotion": "happy"},
        )

    assert response.status_code == 200
    data = response.get_json()
    assert "scan_id" in data
    assert data["scan_id"] == str(fake_id)


# ---------------------------------------------------------------------------
# /practice/result/<scan_id>
# ---------------------------------------------------------------------------


def test_practice_result_no_db(client_no_db):
    """GET /practice/result/<id> returns 500 when DB is None."""
    response = client_no_db.get("/practice/result/507f1f77bcf86cd799439011")
    assert response.status_code == 500
    assert b"No database connection" in response.data


def test_practice_result_not_found(client_with_db, mock_collection):
    """GET /practice/result/<id> returns 404 when scan is missing."""
    mock_collection.find_one.return_value = None
    response = client_with_db.get("/practice/result/507f1f77bcf86cd799439011")
    assert response.status_code == 404
    assert b"not found" in response.data.lower()


def test_practice_result_found(client_with_db, mock_collection):
    """GET /practice/result/<id> returns scan data when found."""
    scan_id = ObjectId()
    mock_collection.find_one.return_value = {
        "_id": scan_id,
        "status": "done",
        "target_emotion": "happy",
        "predicted_emotion": "happy",
        "match_score": 85.0,
        "passed": True,
        "error_message": None,
    }
    response = client_with_db.get(f"/practice/result/{scan_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "done"
    assert data["target_emotion"] == "happy"


def test_practice_result_invalid_id(client_with_db):
    """GET /practice/result/<invalid> returns 500 for bad ObjectId."""
    response = client_with_db.get("/practice/result/not_a_valid_id")
    assert response.status_code == 500


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def test_build_scan_doc(tmp_path):
    """_build_scan_doc returns a dict with expected keys."""
    image_path = tmp_path / "test.jpg"
    doc = _build_scan_doc(image_path, "Happy")
    assert doc["target_emotion"] == "happy"
    assert doc["status"] == "pending"
    assert doc["actor_name"] == "anonymous"
    assert doc["match_score"] is None


def test_save_image(tmp_path):
    """_save_image writes a file and returns its path."""
    image_bytes = base64.b64encode(b"fake_image_content").decode()
    image_data = f"data:image/jpeg;base64,{image_bytes}"

    with patch("app.Path") as mock_path_cls:
        mock_dir = MagicMock()
        mock_path_cls.return_value = mock_dir
        mock_file_path = tmp_path / "happy_test.jpg"
        mock_dir.__truediv__ = lambda s, name: mock_file_path

        result = _save_image(image_data, "happy")
        assert result == mock_file_path
