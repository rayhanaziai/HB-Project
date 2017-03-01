from jinja2 import StrictUndefined
from flask import Flask, render_template, request, flash, redirect, session, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from model import connect_to_db, db, User, Transaction
import requests
import stripe
import json
import datetime
import os
from functions import fetch_user, user_by_email, add_user, fetch_trans, add_trans, new_status, create_charge, create_seller_account, create_seller_token, create_customer, create_transfer
# from sqlalchemy.exc import InvalidRequestError

app = Flask(__name__)
# Required to use Flask sessions and the debug toolbar
app.secret_key = "MYSECRETKEY"

# Normally, if you use an undefined variable in Jinja2, it fails silently.
# This is horrible. Fix this so that, instead, it raises an error.
app.jinja_env.undefined = StrictUndefined

stripe.api_key = os.environ['STRIPE_KEY']

# Use this card number for test purposes 4000 0000 0000 0077
# Account number 000123456789
# Routing number 110000000


def login_required(handler):
    def fn(*a, **kw):
        user_id = session.get('user_id')
        if user_id:
            return handler(user_id, *a, **kw)
        else:
            return redirect('/')
    fn.func_name = handler.func_name
    return fn


@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")


@app.route('/register', methods=['GET'])
def register_form():
    """Show form for user signup."""

    return render_template("register-form.html")


@app.route('/register', methods=['POST'])
def register_process():
    """Process registration."""

    # Get form variables
    fullname = request.form.get("fullname")
    email = request.form.get("email")
    password = request.form.get("password")
    payer_seller = request.form.get("payer_or_receiver")

    # check to see if user already exists. If so, update their details.
    if user_by_email(email) is None:
        current_user = add_user(fullname, email, password, payer_seller)

    else:
        current_user = user_by_email(email)
        current_user.fullname = fullname
        current_user.password = password
        current_user.payer_seller = payer_seller

    db.session.commit()

    flash("User %s added." % fullname)

    session["user_id"] = current_user.user_id
    session["payer_seller"] = current_user.payer_seller
    return redirect("/homepage")


@app.route('/login', methods=['GET'])
def login_form():
    """Show login form."""

    return render_template("login_form.html")


@app.route('/login', methods=['POST'])
def login_process():
    """Process login."""

    # Get form variables
    email = request.form["email"]
    password = request.form["password"]

    user = user_by_email(email)

    if not user:
        flash("No such user")
        return redirect("/login")

    if user.password != password:
        flash("Incorrect password")
        return redirect("/login")

    session["user_id"] = user.user_id
    session["payer_seller"] = user.payer_seller

    flash("Logged in")
    return redirect("/homepage")


@app.route('/logout')
def logout():
    """Log out."""

    del session["user_id"]
    del session["payer_seller"]
    flash("Logged Out.")
    return redirect("/")


@app.route("/homepage", methods=['GET'])
@login_required
def status(user_id):
    """Show info about user."""

    if user_id == session["user_id"]:
        user = fetch_user(user_id)

        if user.payer_seller == "Payer":
            transaction_filter = Transaction.payer_id == user_id
        else:
            transaction_filter = Transaction.seller_id == user_id

        completed_transactions = Transaction.query.filter(
            transaction_filter, Transaction.status == "completed").all()

        pending_transactions = Transaction.query.filter(
            transaction_filter, Transaction.status != "completed").all()

        return render_template("userpage.html",
                               user=user,
                               completed_transactions=completed_transactions,
                               pending_transactions=pending_transactions)
    else:
        flash("Sorry! That's not you!")
        return redirect("/")


@app.route("/homepage", methods=['POST'])
@login_required
def process_acceptance(user_id):
    """Change status of transaction depending on seller acceptance"""

    acceptance = request.form.get("agree_or_disagree")

    transaction_id = session["transaction"]
    current_transaction = fetch_trans(transaction_id)
    seller_user = fetch_user(user_id)
    payer_user = fetch_user(current_transaction.payer_id)

    if acceptance == "agree":
        current_transaction.status = "awaiting payment from payer"
        html = "<html><h2>Easy Pay</h2><br><p>Hi " + payer_user.fullname \
               + ",</p><br>" + seller_user.fullname + " has approved your contract." \
               + "Please<a href='http://localhost:5000/login'><span> log in </span>" \
               + "</a>to make your payment to Easy Pay.<br><br> From the Easy Pay team!</html>"

        # for test purposes, the same buyer email will be used. when live, use '"to": payer_user.email'

        requests.post(
            "https://api.mailgun.net/v3/sandbox9ba71cb39eb046f798ee4676ad972946.mailgun.org/messages",
            auth=('api', 'key-fcaee27772f7acfa5b4246ae675248a0'),
            data={"from": "rayhana.z@hotmail.com",
                  "to": 'buyer.easypay@gmail.com',
                  "subject": "Contract approved!",
                  "html": html})

    else:
        current_transaction.status = "declined by seller"
    db.session.commit()

    # At this stage an email is sent to the buyer with prompt to pay.
    return redirect("/homepage")


@app.route("/terms/<int:user_id>")
@login_required
def transaction_form(user_id):

    user = fetch_user(user_id)
    return render_template("transaction-form.html", user=user)


@app.route("/terms.json", methods=['POST'])
@login_required
def approval_process(user_id):
    """Process approval."""

    # Get form variables
    seller_email = request.form.get("seller_email")
    seller_name = request.form.get("seller_name")
    date = request.form.get("date")
    amount = request.form.get("amount")
    currency = request.form.get("currency")
    print 'DATE:', date
    print type(date)
    date = datetime.datetime.strptime(date, "%Y-%m-%d")

    # The recipient is added to the database
    # password = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    password = 0000
    if user_by_email(seller_email) is None:
        add_user(seller_name, seller_email, password, "Seller")
    else:
        user_by_email(seller_email).payer_seller = "Seller"

    db.session.commit()

    seller = user_by_email(seller_email)
    seller_id = seller.user_id
    payer_id = session['user_id']
    payer = fetch_user(payer_id)
    payer_name = payer.fullname
    # An email is sent to the seller to log in and view the contract

    html = "<html><h2>Easy Pay</h2><br><p>Hi " + seller_name \
        + ",</p><br>" + payer_name + " would like to send you money via Easy Pay. \
        <br> Please<a href='http://localhost:5000/login'><span> log in </span></a>\
        to view and accept the contract:<br>Password: " + str(password) \
        + "<br><br> From the Easy Pay team!</html>"

    # for test purposes, the same seller email will be used. when live, use '"to": seller_email'
    requests.post(
        "https://api.mailgun.net/v3/sandbox9ba71cb39eb046f798ee4676ad972946.mailgun.org/messages",
        auth=('api', 'key-fcaee27772f7acfa5b4246ae675248a0'),
        data={"from": "rayhana.z@hotmail.com",
              "to": 'seller.easypay@gmail.com',
              "subject": "Log in to Easy Pay",
              "html": html})

    # The new transaction is created in the database
    new_transaction = add_trans(payer_id, seller_id, False, False, date, amount, currency, "pending approval from seller")

    date = date.strftime('%Y-%m-%d')

    flash("Approval prompt sent to the recipient")
    # return redirect("/homepage")

    return jsonify({'new_transaction_id': new_transaction.transaction_id,
                    'new_recipient': new_transaction.seller.fullname,
                    'new_date': date,
                    'new_amount': amount,
                    'new_status': "pending approval from seller",
                    'new_action': 'No action'})


@app.route("/approved-form/<int:transaction_id>")
def show_approved_form(transaction_id):

    transaction = fetch_trans(transaction_id)
    user_id = session["user_id"]
    payer_seller = session["payer_seller"]
    session["transaction"] = transaction_id
    return render_template('approved-contract.html',
                           transaction=transaction,
                           user_id=user_id,
                           payer_seller=payer_seller)


@app.route('/payment/<int:transaction_id>')
def payment_form(transaction_id):

    return render_template('payment-form.html',
                           transaction_id=transaction_id)


@app.route('/payment/<int:transaction_id>', methods=['POST'])
def payment_process(transaction_id):

    token = request.form.get("stripeToken")

    transfer = fetch_trans(transaction_id)
    payer_id = transfer.payer_id
    seller_id = transfer.seller_id
    seller_email = transfer.seller.email
    amount = transfer.amount*100
    currency = transfer.currency
    date = transfer.date
    description = "payment from %d to %d" % (payer_id, seller_id)

    # Any way to check if this payment causes error?
    charge = create_charge(amount, token, description)

    if charge.to_dict()['paid'] is not True:
        flash("Your payment has not gone through. Please try again.")
    else:
        new_status(transaction_id, "payment from payer received")

        # As soon as payment is successfull, stripe account set up for seller.
        try:
            new_account = create_seller_account(currency, seller_email)

            account_id = new_account.to_dict()['id']
            s_key = new_account.to_dict()['keys']['secret']

            # Add account_id and s_key to database
            fetch_user(seller_id).account_id = account_id
            fetch_user(seller_id).secret_key = s_key
            db.session.commit()

            #Send prompt email to seller for him to put in account details.
            html = "<html><h2>Easy Pay</h2><br><p>Hi " + transfer.seller.fullname \
                + ",</p><br>" + transfer.payer.fullname + " has transfered the \
                agreed amount of funds to Easy Pay. \
                <br> To get paid on the scheduled date, please log in to your \
                Easy Pay account and enter your account details.\
                <br><br> From the Easy Pay team!</html>"

            # for test purposes, the same seller email will be used. when live, use '"to": seller_email'
            requests.post(
                "https://api.mailgun.net/v3/sandbox9ba71cb39eb046f798ee4676ad972946.mailgun.org/messages",
                auth=('api', 'key-fcaee27772f7acfa5b4246ae675248a0'),
                data={"from": "rayhana.z@hotmail.com",
                      "to": 'seller.easypay@gmail.com',
                      "subject": "Log in to Easy Pay",
                      "html": html})

        except stripe.InvalidRequestError as e:
            flash(e.message)
            # send email to seller telling them to put their details in stripe

    print "***the token is", token
    return redirect("/homepage")


@app.route('/accounts/<int:transaction_id>', methods=['GET'])
def account_form(transaction_id):

    return render_template('account-details-form.html', transaction_id=transaction_id)


@app.route('/accounts/<int:transaction_id>', methods=['POST'])
def account_process(transaction_id):

    name = request.form.get("name")
    routing_number = request.form.get("routing-number")
    account_number = request.form.get("account-number")

    response = create_seller_token(name, routing_number, account_number)

    user_id = session['user_id']
    user = fetch_user(user_id)

    seller_email = user.email
    s_key = user.secret_key
    account_token = response.to_dict()['id']
    amount = fetch_trans(transaction_id).amount
    currency = fetch_trans(transaction_id).currency
    account_id = user.account_id
    print "SECRET KEY:", s_key
    create_customer(seller_email, s_key)
    

    new_status(transaction_id, "payment to seller scheduled")

    return redirect("/homepage")


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app, "postgresql:///easypay")

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(host="0.0.0.0")
