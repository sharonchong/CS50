# C$50 PaperTrade

#### Video Demo: https://youtu.be/5RrCEIf1mP8


## Introduction:
C$50 PaperTrade is a paper trading web application developed as my final project for the Harvard CS50 Introduction to Computer Science course.

Via the web app, users can manage portfolios of stocks. Not only will this tool allow users to check real stocks’ actual prices and portfolios’ values, it will also let users "buy" and “sell” stocks by querying IEX for stocks’ prices.

## Created With
- Python, HTML, Flask, SQL
- Bootstrap, CSS for styling
- IEX API to get the stocks values in real time
- SQL database to store users' information, such as username, a hash of the password, the stocks they bought or sold and transaction history

## Features
1. Register: register for an account
2. Login: login to account
3. Home Page (Portfolio): portfolio overview including stock symbol, shares owned, current price, returns and portfolio allocation of each stock.
4. Quote: obtain stock information such as company name, current price, market cap, P/E ratio, 52-week range and YTD change
5. Buy: buy stocks
6. Sell: sell stocks
7. History: view transaction history
8. Deposit: add cash to account
9. Profile: view user details and change password

## Code Overview
**`application.py`**

Imports CS50’s SQL module and a few helper functions among others.

After configuring Flask, this file configures Jinja with a custom “filter,” usd, a function (defined in helpers.py) that will make it easier to format values as US dollars (USD). It then further configures Flask to store sessions on the local filesystem (i.e., disk) as opposed to storing them inside of (digitally signed) cookies, which is Flask’s default. The file then configures CS50’s SQL module to use finance.db, a SQLite database.

Thereafter are a whole bunch of app routes, most of which support GET and POST. Most routes are “decorated” with @login_required (a function defined in helpers.py too) which ensures that, if a user tries to visit any of those routes, he or she will first be redirected to login so as to log in.

**`helpers.py`** contains utility functions used by the APIs.
- apology: ultimately renders a template, apology.html. It defines within itself another function, escape, that it simply uses to replace special characters in apologies.
- login_required: decorates routes to require login.
- human format: which rounds off given values to the nearest magnitude (K, M, B, T, P). This is applied to the market cap of quoted stocks.
- lookup: given a symbol (e.g., NFLX), returns a stock quote for a company in the form of a dict with three keys: name, whose value is a str, the name of the company; price, whose value is a float; and symbol, whose value is a str, a canonicalized (uppercase) version of a stock’s symbol, irrespective of how that symbol was capitalized when passed into lookup.
- usd: a short function that simply formats a float as USD (e.g., 1234.56 is formatted as $1,234.56).

**`requirements.txt`** prescribes the packages on which this app will depend.

**`static/`** contains CSS styling and other static resources.

**`templates/`** contains HTML templates with Jinja Templating.

**`login.html/`**, **`logout.html/`**, **`register.html/`**, **`index.html/`**, **`quote.html/`**, **`quoted.html/`**, **`buy.html/`**, **`sell.html/`**, **`history.html/`**, **`deposit.html/`**, **`profile.html/`** are all HTML forms, stylized with Bootstrap.

**`apology.html/`** is a template for an apology. Apology in helpers.py takes two arguments: message, which was passed to render_template as the value of bottom, and, optionally, code, which was passed to render_template as the value of top.

**`layout.html/`** comes with a fancy, mobile-friendly “navbar” (navigation bar), also based on Bootstrap. It defines a block, main, inside of which templates go. It also includes support for Flask’s message flashing so which relays messages from one route to another for the user to see.

**`finance.db`** sqlite Database for storing users' details and logging transactions

## Setup
### Steps
1. Clone the repository
2. Install the requirements
    - Flask (pip install flask)
    - cs50 module (pip install cs50)
    - requests module (pip install requests)
3. export FLASK_APP={directory/application.py}
4. Configuring: export API_KEY={IEX API Key - https://iexcloud.io/}
5. Running: flask run
    
### Configuring
- Visit iexcloud.io/cloud-login#/register/.
- Select the “Individual” account type, then enter your email address and a password, and click “Create account”.
- Once registered, scroll down to “Get started for free” and click “Select Start” to choose the free plan.
- Once you’ve confirmed your account via a confirmation email, visit https://iexcloud.io/console/tokens.
- Copy the key that appears under the Token column (it should begin with pk_).
- In your terminal window, execute:
```
$ export API_KEY=value
```
where value is that (pasted) value, without any space immediately before or after the =. You also may wish to paste that value in a text document somewhere, in case you need it again later.

### Running
- Start Flask’s built-in web server (within project/):
```
$ flask run
```
- Visit the URL outputted by flask to see the code in action. 