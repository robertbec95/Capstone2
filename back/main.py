import json
import requests
from flask import Flask, request, jsonify, session
from flask_cors import CORS
#import custom_functions as cp # custom module
from models import db, User, Portfolio
import os
from flask_sqlalchemy import SQLAlchemy
import oracledb
from sqlalchemy.pool import NullPool
#from dotenv import load_dotenv # For retrieving SECRETS
import secrets
from werkzeug.security import generate_password_hash, check_password_hash

#db = SQLAlchemy()

# Load environment variables from .env file
#load_dotenv()

# Flask setup
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config["SECRET_KEY"] = secrets.token_hex(16)
#db = md.db

# Database setup
#db.init_app(app)

# Oracle credentials

un = "ADMIN"
pw = "Capstoneproject123"
dsn = "(description= (retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1521)(host=adb.eu-madrid-1.oraclecloud.com))(connect_data=(service_name=g4bbbc586754471_d9x7y23dgzbr0azz_high.adb.oraclecloud.com))(security=(ssl_server_dn_match=yes)))"
pool = oracledb.create_pool(user=un, password=pw, dsn=dsn)

app.config['SQLALCHEMY_DATABASE_URI'] = 'oracle+oracledb://'
#{un}:{pw}@{dsn}'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'creator': pool.acquire,
    'poolclass': NullPool
}
app.config['SQLALCHEMY_ECHO'] = True
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/stock/<symbol>')
def stock(symbol):
    api_key = "OMLTKM3U67PVKJVJ"
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}"
    response = requests.get(url)

    if response.status_code != 200:
        return "Error: Unable to fetch stock data."

    data = json.loads(response.text)

    if "Error Message" in data:
        return jsonify({"error": data["Error Message"]}), 400

    return jsonify(data)

@app.route("/api/portfolio")
def get_portfolio_summary():
    user = request.args.get("user", "testUser")
    portfolio = {}
    portfolio["username"] = user
    total_port_val = 0
    user_portfolio = db.get_portfolio(username=user)

    portfolio["portfolio"] = {}
    for stock, num_stocks in user_portfolio.items():
        data = cp.get_past_vals(stock, "1d")
        try:
            last_close = cp.get_last_close(data)
        except:
            print("Error in data")
            last_close = float("nan")

        total_port_val += num_stocks * last_close
        portfolio["portfolio"][stock] = {
            "num_stocks": num_stocks,
            "last_close": round(last_close, 2)
        }
    portfolio["total_port_val"] = round(total_port_val, 2)
    return jsonify(portfolio)

@app.route("/api/portfolio/<stock>", methods=['GET'])
def get_stock_values(stock):
    interval = request.args.get("interval", "daily")
    series = cp.get_past_vals(stock, interval)
    past_stock = {"symbol": stock}
    try:
        past_stock["data"] = [
            {"time": x, "value": y}
            for x, y in zip(series["time"], series["close"])
        ]
    except:
        past_stock["data"] = []
    return jsonify(past_stock)

@app.route("/api/login", methods=['POST'])
def login():
    data = request.get_json()
    username = data["username"]
    password = data["password"]

    if md.check_credentials(username, password):
        session["username"] = username
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "Invalid credentials"})

@app.route("/api/logout")
def logout():
    session.pop("username", None)
    return jsonify({"status": "success"})

@app.route("/api/register", methods=['POST'])
def register():
    data = request.get_json()
    username = data["username"]
    password = data["password"]

    if md.check_username_exists(username):
        return jsonify({"status": "error", "message": "Username already exists"})

    md.register_user(username, password)
    return jsonify({"status": "success"})

@app.route("/api/buy", methods=['POST'])
def buy():
    data = request.get_json()
    username = session["username"]
    stock = data["stock"]
    quantity = data["quantity"]

    if not md.check_stock_exists(stock):
        return jsonify({"status": "error", "message": "Stock does not exist"})

    if not md.check_funds(username, quantity * cp.get_last_close(cp.get_past_vals(stock, "min60")["close"])):
        return jsonify({"status": "error", "message": "Insufficient funds"})

    md.buy_stock(username, stock, quantity)
    return jsonify({"status": "success"})

@app.route("/sell", methods=['POST'])
def sell_function():
    data = request.get_json()
    username = session["username"]
    stock = data["stock"]
    quantity = data["quantity"]

    if not md.check_stock_owned(username, stock, quantity):
        return jsonify({"status": "error    if not md.", "message": "You don't own enoughcheck_stock_owned of this stock"})

    md.sell_stock(username, stock, quantity)
    return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(debug=True)