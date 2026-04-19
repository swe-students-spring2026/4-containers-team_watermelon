"""Flask web application for the Actor Emotion Coach platform."""

import base64
import os
from datetime import datetime
from pathlib import Path

import certifi
import pymongo
from bson import ObjectId
from bson.errors import InvalidId
from dotenv import find_dotenv, load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv(find_dotenv())


def _build_scan_doc(image_path, target_emotion):
    """Return a new pending scan document."""
    return {
        "actor_name": "anonymous",
        "image_path": str(image_path.resolve()),
        "target_emotion": target_emotion.lower(),
        "status": "pending",
        "created_at": datetime.now(),
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


def _save_image(image_data, target_emotion):
    """Decode base64 image and save to disk. Returns the file path."""
    _, encoded = image_data.split(",", 1)
    image_bytes = base64.b64decode(encoded)

    output_dir = Path("practice_captures")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{target_emotion.lower()}_{timestamp}.jpg"
    image_path = output_dir / filename

    with open(image_path, "wb") as image_file:
        image_file.write(image_bytes)

    return image_path


def create_app(test_config=None):
    """Application factory to create and configure the Flask app."""
    app = Flask(__name__)  # pylint: disable=redefined-outer-name

    if test_config:
        app.config.update(test_config)

    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("DB_NAME", "emotion_db")
    collection_name = os.getenv("COLLECTION_NAME", "scans")

    app.db = None
    app.collection_name = collection_name

    try:
        connection = pymongo.MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=2000,
            tlsCAFile=certifi.where(),
        )
        connection.server_info()
        app.db = connection[db_name]
    except pymongo.errors.PyMongoError as exc:
        print(f"Failed to connect to MongoDB: {exc}")

    @app.route("/debug")
    def debug():
        """Return all scans for debugging."""
        if app.db is None:
            return {"error": "no db"}

        scans = list(app.db["scans"].find())
        for scan in scans:
            scan["_id"] = str(scan["_id"])
        return jsonify(scans)

    @app.route("/")
    def home():
        """Main dashboard route."""
        emotion_filter = request.args.get("emotion", "all")
        emotions = ["happy", "sad", "angry", "surprise", "neutral", "disgust", "fear"]
        activities = []
        emotion_counts = {e: 0 for e in emotions}
        db_connected = app.db is not None

        if app.db is not None:
            query = {"status": "done"}
            if emotion_filter != "all":
                query["predicted_emotion"] = emotion_filter

            scans = list(
                app.db[app.collection_name].find(query).sort("created_at", -1).limit(20)
            )
            all_done_scans = list(app.db[app.collection_name].find({"status": "done"}))
            for scan in scans:
                activities.append(
                    {
                        "timestamp": scan.get("processed_at") or scan.get("created_at"),
                        "target_emotion": scan.get("target_emotion", ""),
                        "predicted_emotion": scan.get("predicted_emotion", ""),
                        "match_score": scan.get("match_score", 0),
                        "passed": scan.get("passed", False),
                    }
                )
            for scan in all_done_scans:
                predicted = (scan.get("predicted_emotion") or "").lower()
                if predicted in emotion_counts:
                    emotion_counts[predicted] += 1

        return render_template(
            "index.html",
            activities=activities,
            emotions=emotions,
            emotion_filter=emotion_filter,
            emotion_counts=emotion_counts,
            db_connected=db_connected,
        )

    @app.route("/practice")
    def practice_screen():
        """Render the practice screen."""
        return render_template("practice.html")

    @app.route("/practice/submit", methods=["POST"])
    def practice_submit():
        """Accept a captured image and create a pending scan in the database."""
        if app.db is None:
            return jsonify({"error": "No database connection"}), 500

        data = request.get_json()
        image_data = data.get("image_data")
        target_emotion = data.get("target_emotion")

        if not image_data or not target_emotion:
            return jsonify({"error": "Missing image data or target emotion"}), 400

        try:
            image_path = _save_image(image_data, target_emotion)
            scan_doc = _build_scan_doc(image_path, target_emotion)
            inserted = app.db[app.collection_name].insert_one(scan_doc)

            return jsonify(
                {
                    "message": f"Capture submitted for {target_emotion}",
                    "image_path": str(image_path),
                    "scan_id": str(inserted.inserted_id),
                }
            )
        except (OSError, ValueError) as exc:
            return jsonify({"error": str(exc)}), 500

    @app.route("/practice/result/<scan_id>")
    def practice_result(scan_id):
        """Return the processing result for a given scan."""
        if app.db is None:
            return jsonify({"error": "No database connection"}), 500

        try:
            scan = app.db[app.collection_name].find_one({"_id": ObjectId(scan_id)})

            if not scan:
                return jsonify({"error": "Scan not found"}), 404

            scan["_id"] = str(scan["_id"])

            return jsonify(
                {
                    "_id": scan["_id"],
                    "status": scan.get("status"),
                    "target_emotion": scan.get("target_emotion"),
                    "predicted_emotion": scan.get("predicted_emotion"),
                    "match_score": scan.get("match_score"),
                    "passed": scan.get("passed"),
                    "error_message": scan.get("error_message"),
                }
            )
        except (ValueError, KeyError, InvalidId) as exc:
            return jsonify({"error": str(exc)}), 500

    return app


app = create_app()

if __name__ == "__main__":
    flask_port = int(os.getenv("FLASK_PORT", "5001"))
    app.run(host="0.0.0.0", port=flask_port)
