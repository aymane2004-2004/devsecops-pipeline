"""API Flask minimale et sécurisée, cible du pipeline DevSecOps."""
import os
import re
from threading import Lock

from flask import Flask, jsonify, request

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024  # 16 KiB max par requête

# Stockage en mémoire (suffisant pour la démo, thread-safe avec un verrou)
_items: dict[int, dict] = {}
_next_id = 1
_lock = Lock()

NAME_PATTERN = re.compile(r"^[\w\s\-\.]{1,64}$", re.UNICODE)


@app.after_request
def add_security_headers(response):
    """En-têtes HTTP de sécurité (corrigent les alertes ZAP passives)."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; frame-ancestors 'none'"
    )
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers.pop("Server", None)
    return response


@app.get("/")
def index():
    return jsonify(service="devsecops-demo-api", version="1.0.0")


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/api/items")
def list_items():
    with _lock:
        return jsonify(list(_items.values()))


@app.post("/api/items")
def create_item():
    global _next_id
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="JSON object attendu"), 400

    name = data.get("name")
    if not isinstance(name, str) or not NAME_PATTERN.match(name):
        return jsonify(error="'name' invalide (1-64 caractères alphanumériques)"), 400

    with _lock:
        item = {"id": _next_id, "name": name.strip()}
        _items[_next_id] = item
        _next_id += 1
    return jsonify(item), 201


@app.get("/api/items/<int:item_id>")
def get_item(item_id: int):
    with _lock:
        item = _items.get(item_id)
    if item is None:
        return jsonify(error="introuvable"), 404
    return jsonify(item)


@app.errorhandler(404)
def not_found(_e):
    return jsonify(error="introuvable"), 404


@app.errorhandler(405)
def method_not_allowed(_e):
    return jsonify(error="méthode non autorisée"), 405


@app.errorhandler(413)
def too_large(_e):
    return jsonify(error="requête trop volumineuse"), 413


@app.errorhandler(500)
def server_error(_e):
    # Jamais de stack trace exposée au client
    return jsonify(error="erreur interne"), 500


if __name__ == "__main__":
    # Lancement local uniquement. En conteneur : gunicorn (voir Dockerfile).
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")))
