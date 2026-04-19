"""MongoDB helper functions for acting-attempt processing."""

from datetime import datetime, timezone

import certifi
from pymongo import MongoClient, ReturnDocument

from app.config import COLLECTION_NAME, DB_NAME, MONGO_URI

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client[DB_NAME]
scans = db[COLLECTION_NAME]


def utc_now():
    """Return the current UTC time."""
    return datetime.now(timezone.utc)


def create_pending_scan(image_path, target_emotion, actor_name="anonymous"):
    """Insert a new acting attempt waiting to be processed."""
    if not image_path:
        raise ValueError("image_path is required")
    if not target_emotion:
        raise ValueError("target_emotion is required")

    result = scans.insert_one(
        {
            "actor_name": actor_name,
            "image_path": image_path,
            "target_emotion": target_emotion.lower(),
            "status": "pending",
            "created_at": utc_now(),
            "started_at": None,
            "processed_at": None,
            "predicted_emotion": None,
            "emotion_scores": None,
            "match_score": None,
            "passed": None,
            "face_detected": None,
            "processing_time_ms": None,
            "error_message": None,
        }
    )
    return result.inserted_id


def get_next_pending_scan():
    """Find one pending scan and mark it as processing."""
    return scans.find_one_and_update(
        {"status": "pending"},
        {"$set": {"status": "processing", "started_at": utc_now()}},
        return_document=ReturnDocument.AFTER,
    )


def mark_scan_done(scan_id, result):
    """Mark a scan as completed and store analysis results."""
    scans.update_one(
        {"_id": scan_id},
        {
            "$set": {
                "status": "done",
                "processed_at": utc_now(),
                "predicted_emotion": result["predicted_emotion"],
                "emotion_scores": result["emotion_scores"],
                "match_score": result["match_score"],
                "passed": result["passed"],
                "face_detected": result["face_detected"],
                "processing_time_ms": result["processing_time_ms"],
                "error_message": None,
            }
        },
    )


def mark_scan_error(scan_id, message):
    """Mark a scan as failed and store the error message."""
    scans.update_one(
        {"_id": scan_id},
        {
            "$set": {
                "status": "error",
                "processed_at": utc_now(),
                "predicted_emotion": None,
                "emotion_scores": None,
                "match_score": 0.0,
                "passed": False,
                "face_detected": False,
                "processing_time_ms": None,
                "error_message": message,
            }
        },
    )
