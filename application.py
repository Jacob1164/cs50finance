# Jacob Frabutt
# 8-4-18
# Thanks to stackoverflow for helping me through a couple minor issues


import os

from cs50 import SQL, eprint
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False

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


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # Query database for stocks
    rows = db.execute("SELECT * FROM current WHERE user_id = :idd",
                      idd=session["user_id"])

    current, tot, trend = [], [], []
    total = 0

    # check current cash
    cash = db.execute("SELECT * FROM users WHERE id = :idd",
                      idd=session["user_id"])[0]
    total += cash["cash"]

    return render_template("index.html", rows=rows, cash=cash["fcash"], total=usd(total), current=current, length=len(rows), tot=tot, trend=trend)


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    """Account info"""
    if request.method == "POST":
        # fill in form?
        if not request.form.get("old"):
            return apology("Must provide previous password", 400)
        if not request.form.get("new"):
            return apology("Must provide new password", 400)
        if not request.form.get("confirm"):
            return apology("Must re-enter password", 400)

        row = db.execute("SELECT * FROM users WHERE id = :idd",
                          idd=session["user_id"])

        if not check_password_hash(row[0]["hash"], request.form.get("old")):
            return apology("current password is incorrect", 400)

        if not request.form.get("new") == request.form.get("confirm"):
            return apology("passwords don't match", 400)

        db.execute("UPDATE users SET hash = :passw WHERE id = :idd",
                   passw=generate_password_hash(request.form.get("new")), idd=session["user_id"])

        return redirect("/")

    else:
        name = db.execute("SELECT username FROM users WHERE id = :idd",
                          idd=session["user_id"])[0]["username"]
        return render_template("account.html", name=name)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        # convert to int and check
        try:
            shares = int(request.form.get("shares"))
        except ValueError:
            return apology("Shares must be a positive integer", 400)

        if shares <= 0:
            return apology("Shares must be a positive integer", 400)

        # get the price and other info
        info = lookup(request.form.get("symbol"))
        if info == None:
            return apology("Not a valid symbol", 400)
        price = info["price"]
        symbol = info["symbol"]
        name = info["name"]
        subout = price * shares

        # check current cash
        cash = db.execute("SELECT cash FROM users WHERE id = :idd",
                          idd=session["user_id"])[0]["cash"]

        # make sure if is affordable
        if cash - subout < 0:
            return apology("Can not be afforded", 403)
        else:
            cash -= subout

        # update cash amount
        db.execute("UPDATE users SET cash=:cash, fcash=:fcash WHERE id = :idd",
                   cash=cash, fcash=usd(cash), idd=session["user_id"])

        # Get current stocks
        rows = db.execute("SELECT * FROM current WHERE user_id = :idd",
                          idd=session["user_id"])
        already = False

        # check if this stock is already owned
        for row in rows:
            if row["symbol"] == symbol:
                already = True
                newtot = row["total"] + subout
                newshares = row["shares"] + shares

        # add it to the database
        if already:
            db.execute("UPDATE current SET shares = :shares, total = :ntotal, price = :price, format_price = :fprice, format_total = :ftotal WHERE user_id = :idd AND symbol = :symbol",
                       shares=newshares, ntotal=newtot, price=price, fprice=usd(price), ftotal=usd(newtot), idd=session["user_id"], symbol=symbol)
        else:
            db.execute("INSERT INTO current (user_id, symbol, name, shares, price, total, format_price, format_total) VALUES (:idd, :symbol, :name, :shares, :price, :total, :fprice, :ftotal)",
                       idd=session["user_id"], symbol=symbol, name=name, shares=shares, price=price, total=subout, fprice=usd(price), ftotal=usd(subout))

        # add it to the history
        db.execute("INSERT INTO history (user_id, symbol, shares, price, Action, cum_sum) VALUES (:idd, :symbol, :shares, :price, :action, :s)",
                   idd=session["user_id"], symbol=symbol, shares=shares, price=usd(price), action="Bought", s=usd(cash))

        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    if request.method == "POST":
        db.execute("DELETE FROM current WHERE user_id = :idd",
                       idd=session["user_id"])
        db.execute("DELETE FROM history WHERE user_id = :idd",
                       idd=session["user_id"])
        db.execute("DELETE FROM users WHERE id = :idd",
                       idd=session["user_id"])
        return redirect("/login")
    else:
        return render_template("warn.html")

@app.route("/check", methods=["GET", "POST"])
@login_required
def check():
    return render_template("warn.html")



@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    rows = db.execute("SELECT * FROM history WHERE user_id = :idd",
                      idd=session["user_id"])

    return render_template("history.html", rows=rows)


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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["user_name"] = rows[0]["username"]

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
    if request.method == "POST":
        # call lookup function
        info = lookup(request.form.get("symbol"))

        if info == None:
            return apology("invalid symbol", 400)

        # isolate variables
        name = info["name"]
        price = usd(info["price"])
        symbol = info["symbol"]

        return render_template("quoted.html", name=name, price=price, symbol=symbol)

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # check username
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # check if already used
        if len(rows) != 0:
            return apology("username already in use", 400)

        # check password
        if not request.form.get("password"):
            return apology("must provide password", 400)
        if not request.form.get("confirmation"):
            return apology("must re-enter password", 400)
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 400)

        # hash password
        word = generate_password_hash(request.form.get("password"))

        # add it to the database
        db.execute("INSERT INTO users (username, hash, cash, fcash) VALUES (:username, :password, :cash, :fcash)",
                   username=request.form.get("username"), password=word, cash=20000, fcash="$20,000.00")

        return redirect("/login")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        # values
        sym = request.form.get("symbol")
        shares = int(request.form.get("shares"))

        # positive number
        if shares <= 0:
            return apology("shares must be a positive integer", 400)

        # access current stocks
        rows = db.execute("SELECT * FROM current WHERE user_id = :idd AND symbol = :sym",
                          idd=session["user_id"], sym=sym)
        new = rows[0]["shares"] - shares

        price = lookup(sym)["price"]

        # will this delete a line or not or error
        if new > 0:
            db.execute("UPDATE current SET shares=:new, total=:newtot, format_total=:fnewtot WHERE user_id = :idd AND symbol = :sym",
                       new=new, newtot=new * price, fnewtot=usd(new * price), idd=session["user_id"], sym=sym)
        elif new == 0:
            db.execute("DELETE FROM current WHERE user_id = :idd AND symbol = :sym",
                       idd=session["user_id"], sym=sym)
        else:
            return apology("You don't have that many shares", 400)

        # check current cash
        cash = db.execute("SELECT cash FROM users WHERE id = :idd",
                          idd=session["user_id"])[0]["cash"]
        add = price * shares
        cash += add

        # update cash amount
        db.execute("UPDATE users SET cash=:cash WHERE id = :idd",
                   cash=cash, idd=session["user_id"])
        db.execute("UPDATE users SET fcash=:cash WHERE id = :idd",
                   cash=usd(cash), idd=session["user_id"])

        # add it to the history
        db.execute("INSERT INTO history (user_id, symbol, shares, price, Action, cum_sum) VALUES (:idd, :symbol, :shares, :price, :action, :s)",
                   idd=session["user_id"], symbol=sym, shares=shares, price=usd(price), action="Sold", s=usd(cash))

        return redirect("/")

    else:
        rows = db.execute("SELECT * FROM current WHERE user_id = :idd",
                          idd=session["user_id"])
        return render_template("sell.html", rows=rows)


@app.route("/update")
@login_required
def update():
    rows = db.execute("SELECT * FROM current WHERE user_id = :idd",
                      idd=session["user_id"])
    send = []
    total = db.execute("SELECT * FROM users WHERE id = :idd",
                      idd=session["user_id"])[0]["cash"]
    for row in rows:
        price = lookup(row["symbol"])["price"]
        if price - row["price"] < 0:
            color = "red"
        elif price == row["price"]:
            color = "black"
        else:
            color = "green"

        total += row["shares"] * price
        send.append({"price": usd(price), "color": color, "tot": usd(row["shares"] * price), "total": usd(total), "bal": total})

    return jsonify(send)

# def errorhandler(e):
    # """Handle error"""
   #  return apology(e.name, e.code)


# listen for errors
# for code in default_exceptions:
    # app.errorhandler(code)(errorhandler)
