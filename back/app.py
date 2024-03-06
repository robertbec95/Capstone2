import requests
import json
from flask import Flask, jsonify, render_template, url_for
from flask_cors import CORS

#Initialize the Flask app
app = Flask(__name__)
CORS(app)

with open("database.json", "r") as file: #Load database from JSON file
    database = json.load(file)

def get_latest_quote(symbol): #Function to fetch the latest stock quote
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

@app.route('/') #Route for homepage
def homepage():
    featured_symbols = ["MSFT", "AAPL", "GOOGL", "TSLA", "NVDA"]
    latest_quotes = {symbol: get_latest_quote(symbol) for symbol in featured_symbols}
    return render_template("homepage.html", featured_symbols=featured_symbols, latest_quotes=latest_quotes)

@app.route('/stock/<symbol>') #Route for fetching stock data
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


@app.route('/user/<user_id>') #Route for fetching user data
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

@app.route('/portfolio/<user_id>') #Route for rendering user portfolio
def portfolio(user_id):
    if user_id not in database:
        return jsonify({"error": "User not found."}), 400

    user_data = database[user_id]
    total_stock_value = 0
    holdings = []

    for symbol, weight in zip(user_data["symbols"], user_data["weights"]): #Fetch stock data for each symbol
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

if __name__ == '__main__': #Run the app
    app.run(debug=True)

    for user_id in database:  #Print the URL for each user's portfolio
        print(url_for('portfolio', user_id=user_id))