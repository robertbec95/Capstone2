import requests
import json
from flask import Flask, jsonify, render_template, url_for
from flask_cors import CORS

# Initialize the Flask app
app = Flask(__name__)
CORS(app)

# Load the database contents
with open("database.json", "r") as file:
    database = json.load(file)

### Oracle database credentials
#un = "ADMIN"
#pw = "Capstoneproject123"
#dsn = "(description= (retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1521)(host=adb.eu-madrid-1.oraclecloud.com))(connect_data=(service_name=g4bbbc586754471_d9x7y23dgzbr0azz_high.adb.oraclecloud.com))(security=(ssl_server_dn_match=yes)))"
#pool = oracledb.create_pool(user=un, password=pw, dsn=dsn) # Create a connection pool to the Oracle database

# Configure SQLAlchemy with the Oracle database URI and options
#app.config['SQLALCHEMY_DATABASE_URI'] = 'oracle+oracledb://'
#{un}:{pw}@{dsn}'
#app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    #'creator': pool.acquire,
   # 'poolclass': NullPool
#}
# Enable SQLALCHEMY to echo queries to the console
#app.config['SQLALCHEMY_ECHO'] = True
#db.init_app(app)

# Function to get the latest quote for a given stock symbol
def get_latest_quote(symbol):
    api_key = "OMLTKM3U67PVKJVJ"
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
    response = requests.get(url)

    if response.status_code != 200:
        return None

    data = response.json()
    if "Global Quote" not in data:
        return None

    if "Error Message" in data["Global Quote"]:
        return None
    
    return data["Global Quote"]

# Route for the homepage
@app.route('/')
def homepage():
    featured_symbols = ["MSFT", "AAPL", "GOOGL", "TSLA", "NVDA"]
    latest_quotes = {symbol: get_latest_quote(symbol) for symbol in featured_symbols}
    return render_template("homepage.html", featured_symbols=featured_symbols, latest_quotes=latest_quotes)

# Route to get information for a specific stock
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

# Route to get user information by user_id
@app.route('/user/<user_id>')
def user(user_id):
    if user_id not in database:
        return jsonify({"error": "User not found."}), 400

    user_data = database[user_id]
    total_stock_value = 0
    holdings = []

    for symbol, weight in zip(user_data["symbols"], user_data["weights"]):
        api_key = "OMLTKM3U67PVKJVJ"
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}"
        response = requests.get(url)

        if response.status_code != 200:
            return "Error: Unable to fetch stock data."

        stock_data = json.loads(response.text)

        if "Error Message" in stock_data:
            return jsonify({"error": stock_data["Error Message"]}), 400

        latest_date = list(stock_data["Time Series (Daily)"].keys())[-1]

        stock_value = float(stock_data["Time Series (Daily)"][latest_date]["4. close"]) * weight
        total_stock_value += stock_value

        holdings.append({"symbol": symbol, "stock_value": stock_value})

    return jsonify({"user_id": user_id, "total_stock_value": total_stock_value, "holdings": holdings})

# Define the route for user portfolio pages
@app.route('/portfolio/<user_id>')
def portfolio(user_id):
    if user_id not in database:
        return jsonify({"error": "User not found."}), 400

    user_data = database[user_id]
    total_stock_value = 0
    holdings = []

    for symbol, weight in zip(user_data["symbols"], user_data["weights"]):
        api_key = "OMLTKM3U67PVKJVJ"
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}"
        response = requests.get(url)

        if response.status_code != 200:
            return "Error: Unable to fetch stock data."

        stock_data = json.loads(response.text)

        if "Error Message" in stock_data:
            return jsonify({"error": stock_data["error"]["message"]}), 400

        latest_date = list(stock_data["Time Series (Daily)"].keys())[-1]

        stock_value = float(stock_data["Time Series (Daily)"][latest_date]["4. close"]) * weight
        total_stock_value += stock_value

        holdings.append({"symbol": symbol, "stock_value": stock_value})

    return render_template('portfolio.html', user_id=user_id, total_stock_value=total_stock_value, holdings=holdings)

if __name__ == '__main__':
    app.run(debug=True)

    for user_id in database:
        print(url_for('portfolio', user_id=user_id))