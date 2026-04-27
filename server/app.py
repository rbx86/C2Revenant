"""
app.py — C2 server entry point.

Run with:
    python app.py
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from flask import Flask
from flask_cors import CORS

import config
import db
from routes import beacon_bp


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    # Initialise database
    db.init_db()

    # Register blueprints
    app.register_blueprint(beacon_bp)

    return app


if __name__ == "__main__":
    app = create_app()

    print("=" * 60)
    print("  C2 SERVER")
    print(f"  Listening on http://{config.HOST}:{config.PORT}")
    print(f"  Database: {config.DB_PATH}")
    print("=" * 60)
    print("  Waiting for beacons...\n")

    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
