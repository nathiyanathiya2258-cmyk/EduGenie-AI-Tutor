from pathlib import Path
import os
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(_file_).parent
INDEX = ROOT / "static" / "index.html"
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

MODES = {
    "Tutor": "Explain concepts clearly, check understanding, and guide the learner with examples.",  "Study buddy": "Be an encouraging study partner. Break work into small steps and help the learner stay focused.",
    "Quiz me": "Ask one question at a time. Wait for the learner's answer before revealing or explaining the solution.",
    "Explain simply": "Use plain language, short sentences, and a concrete everyday analogy. Avoid unnecessary jargon."
}

def make_gemini_request(message, mode, history):
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "Add your Gemini API key in terminal first."

    if not message or not message.strip():
        return "Write a question first."   if len(message) > 4000:
        return "Questions must be 4,000 characters or fewer."

    prompt = f"{MODES.get(mode, MODES['Tutor'])}\n\nUser question: {message}"

    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}]
    }

    req = Request(
        API_URL + f"?key={api_key}",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except HTTPError as e:
        err = e.read().decode("utf-8")
        return f"Gemini API error {e.code}: {err[:500]}"except Exception as e:
        return f"Error: {e}"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(INDEX.read_bytes())
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/chat":
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            msg = payload.get("message", "")
            mode = payload.get("mode", "Tutor")
            history = payload.get("history", [])reply = make_gemini_request(msg, mode, history)

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"reply": reply}).encode("utf-8"))
        else:
            self.send_error(404)

if _name_ == "_main_":
    httpd = HTTPServer(("127.0.0.1", 8000), Handler)
    print("EduGenie is ready at http://127.0.0.1:8000")
    httpd.serve_forever()