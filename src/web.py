from datetime import datetime
from flask import Flask, jsonify, request
from src.views import events_page, main_page

app = Flask(__name__)

@app.route("/")
def index():
    return jsonify({
        "message": "Bank transaction analysis API",
        "endpoints": {
            "/api/main": "JSON для главной страницы",
            "/api/events": "JSON для страницы событий",
        }
    })

@app.route("/api/main")
def api_main():
    date_time = request.args.get("date_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    transactions_path = request.args.get("transactions_path", "data/operations.xlsx")
    return jsonify(main_page(date_time=date_time, transactions_path=transactions_path))

@app.route("/api/events")
def api_events():
    date = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    period = request.args.get("period", "M")
    transactions_path = request.args.get("transactions_path", "data/operations.xlsx")
    return jsonify(events_page(date=date, period=period, transactions_path=transactions_path))

@app.errorhandler(FileNotFoundError)
def handle_file_not_found(error):
    return jsonify({"error": str(error)}), 404

@app.errorhandler(ValueError)
def handle_value_error(error):
    return jsonify({"error": str(error)}), 400