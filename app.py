from flask import Flask
import threading
from bot_manager import start_enterprise_bot

app = Flask(__name__)

started = False

@app.route("/")
def home():
    return "✅ Enterprise Amazon Bot Running"

@app.route("/health")
def health():
    return {"status": "OK"}

def boot():
    global started
    if not started:
        start_enterprise_bot()
        started = True

threading.Thread(target=boot, daemon=True).start()
