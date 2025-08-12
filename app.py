from flask import Flask, redirect, jsonify, request, session
from ai import get_html_from_ai, get_index_from_ai
from apscheduler.schedulers.background import BackgroundScheduler
import waitress
import secrets
from functools import wraps

LOGGING = False

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)

def reset_rate_limit(app):
    with app.app_context():
        import secrets
        app.config['SECRET_KEY'] = secrets.token_hex(16) # Workaround to clear all sessions

scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(func=lambda: reset_rate_limit(app), trigger="interval", hours=12)

reset_rate_limit(app)

def rate_limit_decorator(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if session.get("rate_limit", False):
            session["rate_limit"] += 1
            if session["rate_limit"] > 250:
                return redirect('/rate_limit')
        else:
            session["rate_limit"] = 1
        return func(*args, **kwargs)
    return decorated_function

def append_html_to_log(html, route):
    if not LOGGING:
        return
    with open("app.log", "a") as log_file:
        log_file.write(f"HTML generated for {route}:\n")
        log_file.write(html + "\n")

@app.route('/')
@rate_limit_decorator
def home():
    print("Rendering index.html")
    html = get_index_from_ai()
    append_html_to_log(html, "index")
    return html

@app.route('/rate_limit')
def rate_limit():
    return jsonify({"message": "Rate limit reached. Please try again later. Cleared every 12 hours."}), 429

@app.route('/settings', methods=['POST'])
@rate_limit_decorator
def settings():
    print("Settings endpoint called")
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    if data['temperature']:
        session["temperature"] = data['temperature']
    if data['max_completion_tokens']:
        session["max_completion_tokens"] = data['max_completion_tokens']
    if data['creative_JS']:
        session["creative_JS"] = data['creative_JS']
    if data['rewise_html']:
        session["rewise_html"] = data['rewise_html']
    print(f"Received settings: {data}")
    return jsonify(data)

@app.route('/<path:route>')
@rate_limit_decorator
def dynamic_route(route):
    if route == 'settings':
        return redirect('/settings')
    if route == '':
        return redirect('/')
    print(f"Dynamic route accessed: {route}")
    html = get_html_from_ai(route=route, temperature=session.get("temperature", 1), max_tokens=session.get("max_completion_tokens", 1024), creative=session.get("creative_JS", False), look_over=session.get("rewise_html", False))
    append_html_to_log(html, route)
    return html


if __name__ == '__main__':
    waitress.serve(app, host="0.0.0.0", port=5000)