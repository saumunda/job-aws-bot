# =========================
# 1. Imports
# =========================
from flask import Flask
import threading
from bot_manager import start_enterprise_bot


# =========================
# 2. App Initialization
# =========================
app = Flask(__name__)


# =========================
# 3. Global State
# =========================
started = False


# =========================
# 4. Routes
# =========================
@app.route("/")
def home():
    return "✅ Enterprise Amazon Bot Running"


@app.route("/health")
def health():
    return {"status": "OK"}


# =========================
# 5. Background Boot Logic
# =========================
def boot():
    global started
    if not started:
        start_enterprise_bot()
        started = True


# =========================
# 6. Start Background Thread
# =========================
threading.Thread(target=boot, daemon=True).start()
