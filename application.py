import os
import re

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd, human_format

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # query stock positions
    positions = db.execute(
        "SELECT symbol, SUM(shares) AS shares, AVG(price) AS price FROM transactions WHERE user_id = ? GROUP BY symbol HAVING SUM(shares) > 0", session["user_id"])

    # calculate attributes for stock
    grand_total = 0
    total_return = 0

    for stock in positions:
        symbol = stock["symbol"]
        shares = stock["shares"]
        quote = lookup(symbol)
        stock["name"] = quote["name"]
        stock["current_price"] = quote["price"]
        stock["total"] = float(stock["current_price"] * shares)
        stock["var"] = stock["current_price"] - stock["price"]
        stock["return"] = float(stock["var"] * shares)
        stock["returnpct"] = "{:.2%}".format(stock["return"] / stock["total"])
        grand_total += stock["total"]
        total_return += stock["return"]

    # query cash value
    user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    cash = user[0]["cash"]

    # calculate total
    grand_total += cash
    total_returnpct = "{:.2%}".format(total_return / grand_total)
    cash_weight = "{:.2%}".format(cash / grand_total)
    
    for stock in positions:
        stock["weight"] = "{:.2%}".format(stock["total"] / grand_total)

    return render_template("index.html", positions=positions, cash=cash, cash_weight=cash_weight, grand_total=grand_total, total_return=total_return, total_returnpct=total_returnpct)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    # get: display form to buy stock
    if request.method == "GET":

        return render_template("buy.html")

    # post: purchase stock so long as the user can afford it (compare with cash)
    if request.method == "POST":

        # Ensure valid input
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        # Ensure symbol is valid
        if lookup(symbol) == None:
            return apology("must provide valid symbol", 400)

        # Check if number is a positive integer
        try:
            int(shares)
        except ValueError:
            return apology("Enter valid amount of shares", 400)

        shares = int(shares)
        if shares < 1:
            return apology("Number of shares must be a positive integer!", 400)

        # Check if user can afford it
        quoted = lookup(symbol)
        total_price = quoted["price"] * int(shares)
        user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        cash = user[0]["cash"]

        if total_price > cash:
            return apology("not enough cash", 400)

        # Insert into transactions table
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        message = "Bought!"

        db.execute(
            "INSERT INTO transactions (user_id, symbol, shares, price, transaction_type, datetime) VALUES(?, ?, ?, ?, ?, ?)",
            session["user_id"], symbol, shares, quoted["price"], "BUY", dt_string)

        # update cash in users table
        updated_cash = cash - total_price
        db.execute("UPDATE users SET cash = ? WHERE id = ?", updated_cash, session["user_id"])
    
    flash("Bought!")
    return redirect("/")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # display a table with a history of all transactions, listing row by row each buy and sell
    # query stock positions
    positions = db.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY datetime DESC", session["user_id"])

    return render_template("history.html", positions=positions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    # get: display form to request stock quote
    if request.method == "GET":

        return render_template("quote.html")

    # post: lookup stock symbol via lookup() and display results
    else:
        symbol = request.form.get("symbol")

        # if lookup()="None", return error msg
        if lookup(symbol) == None:
            return apology("must provide valid symbol", 400)

        quoted = lookup(symbol)
        marketCap_rounded = human_format(quoted["marketCap"])
        return render_template("quoted.html", quoted=quoted, marketCap_rounded=marketCap_rounded)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # get: display registration form (username, pw, pw confirmation)
    if request.method == "GET":

        return render_template("register.html")

    # post: insert new user into users table
    else:

        username = request.form.get("username")
        password = request.form.get("password")

        reg = re.compile("^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{6,}$")

        # check for invalid inputs
        # Ensure username is not blank
        if not username:
            return apology("must provide username", 400)

        # Ensure username does not already exist
        rows = db.execute("SELECT DISTINCT(username) FROM users WHERE username = ?", username)
        if len(rows) != 0:
            return apology("username taken", 400)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 400)

        elif not re.search(reg, password):
            return apology("password must be between 6 characters long; contain at least 1 number, 1 letter and 1 special character", 400)

        # Ensure passwords match
        elif not request.form.get("confirmation") == password:
            return apology("passwords must match", 400)

        # Hash password
        hash = generate_password_hash(password)

        # Insert into users table
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hash)

    # direct to login page
    return render_template("login.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # get: display form to sell stock
    if request.method == "GET":

        # query stock positions
        positions = db.execute(
            "SELECT symbol, SUM(shares) AS shares_owned FROM transactions WHERE user_id = ? GROUP BY symbol HAVING shares_owned > 0", session["user_id"])
        return render_template("sell.html", positions=positions)

    # post: sell specified number of shares of stock, update user's cash
    else:

        symbol = request.form.get("symbol")
        shares_sold = int(request.form.get("shares"))

        # Ensure user selects stock
        if not symbol:
            return apology("must select stock", 400)

        # Ensure user enters shares
        elif not shares_sold:
            return apology("must provide number of shares", 400)

        # Ensure user owns stock
        stock_to_sell = db.execute(
            "SELECT symbol, SUM(shares) AS shares_owned FROM transactions WHERE symbol = ? AND user_id = ? GROUP BY symbol HAVING shares_owned > 0", symbol, session['user_id'])
        if len(stock_to_sell) == 0:
            return apology("you do not own any of this stock!", 400)

        # Ensure user owns number of shares
        elif shares_sold > int(stock_to_sell[0]["shares_owned"]):
            return apology("you do not own enough of this stock to sell", 400)

        # Insert into transactions table
        quoted = lookup(symbol)
        total_price = quoted["price"] * shares_sold
        shares_sold = shares_sold * -1
        user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        cash = user[0]["cash"]

        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

        db.execute(
            "INSERT INTO transactions (user_id, symbol, shares, price, transaction_type, datetime) VALUES(?, ?, ?, ?, ?, ?)",
            session["user_id"], symbol, (shares_sold), quoted["price"], "SELL", dt_string)

        # update cash in users table
        updated_cash = cash + total_price
        db.execute("UPDATE users SET cash = ? WHERE id = ?", updated_cash, session["user_id"])
    
    flash("Sold!")
    return redirect("/")


@app.route("/profile", methods=["GET", "POST"])
@login_required
# profile page showing username and to change password
def profile():
    # get: display change password form
    if request.method == "GET":

        rows = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
        username = rows[0]["username"]
        
        return render_template("profile.html", username=username)

    # post: update password in users
    else:

        new_password = request.form.get("new_password")
        reg = re.compile("^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{6,}$")

        # check for invalid inputs
        # Ensure new password is not blank
        if not new_password:
            return apology("must provide new password", 400)

        elif not re.search(reg, new_password):
            return apology("password must be between 6 characters long; contain at least 1 number, 1 letter and 1 special character", 400)

        # Ensure new passwords match
        elif not request.form.get("new_password_confirmation") == new_password:
            return apology("new passwords must match", 400)

        # Hash new password
        new_hash = generate_password_hash(new_password)

        # Insert into users table
        db.execute("UPDATE users SET hash = ? WHERE id = ?", new_hash, session["user_id"])
        
        flash("Password changed!")
        return redirect("/")


@app.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    # get: display deposit form
    if request.method == "GET":
        
        return render_template("deposit.html")

    # post: update cash in users
    else:
        
        deposit = float(request.form.get("deposit"))
        
        # update cash in users table
        user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        cash = user[0]["cash"]
        updated_cash = cash + deposit
        
        db.execute("UPDATE users SET cash = ? WHERE id = ?", updated_cash, session["user_id"])
    
    flash("Cash deposited!")
    return redirect("/")
        
        
def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
