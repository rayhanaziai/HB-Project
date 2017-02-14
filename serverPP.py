from jinja2 import StrictUndefined

from flask import Flask, render_template, request, flash, redirect, session
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, User, Transaction
import urllib
import requests
import os
import paypalrestsdk
import stripe
import json
import datetime

app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "MYSECRETKEY"

# Normally, if you use an undefined variable in Jinja2, it fails silently.
# This is horrible. Fix this so that, instead, it raises an error.
app.jinja_env.undefined = StrictUndefined
stripe.api_key = "sk_test_uXpQmqM8CWnoWDgkKQJUFcDZ"


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

    new_user = User(fullname=fullname, email=email, password=password, payer_seller=payer_seller)

    db.session.add(new_user)
    db.session.commit()

    flash("User %s added." % fullname)

    session["user_id"] = new_user.user_id
    session["payer_seller"] = new_user.payer_seller
    return redirect("/homepage/%s" % new_user.user_id)

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

    user = User.query.filter_by(email=email).first()

    if not user:
        flash("No such user")
        return redirect("/login")

    if user.password != password:
        flash("Incorrect password")
        return redirect("/login")

    session["user_id"] = user.user_id
    session["payer_seller"] = user.payer_seller

    flash("Logged in")
    return redirect("/homepage/%s" % user.user_id)


@app.route('/logout')
def logout():
    """Log out."""

    del session["user_id"]
    flash("Logged Out.")
    return redirect("/")


@app.route("/homepage/<int:user_id>", methods=['GET'])
def status(user_id):
    """Show info about user."""

    user = User.query.get(user_id)

    if user.payer_seller == "payer":
        transactions = Transaction.query.filter(Transaction.payer_id == user_id).all()
        completed_transactions = Transaction.query.filter(Transaction.payer_id == user_id, Transaction.status == "completed").all()
        pending_transactions = Transaction.query.filter(Transaction.payer_id == user_id, Transaction.status != "completed").all()
    else:
        transactions = Transaction.query.filter(Transaction.seller_id == user_id).all()
        completed_transactions = Transaction.query.filter(Transaction.seller_id == user_id, Transaction.status == "completed").all()
        pending_transactions = Transaction.query.filter(Transaction.seller_id == user_id, Transaction.status != "completed").all()

    return render_template("userpage.html",
                           user=user,
                           transactions=transactions,
                           completed_transactions=completed_transactions,
                           pending_transactions=pending_transactions)


@app.route("/homepage/<int:user_id>", methods=['POST'])
def process_acceptance(user_id):
    """Change status of transaction depending on seller acceptance"""

    acceptance = request.form.get("agree_or_disagree")

    transaction_id = session["transaction"]
    current_transaction = Transaction.query.get(transaction_id)

    if acceptance == "agree":
        current_transaction.status = "Awaiting payment from payer"
    else:
        current_transaction.status = "Declined by seller"
    db.session.commit()

    # At this stage an email is sent to the buyer with prompt to pay.
    return redirect("/homepage/%s" % user_id)


@app.route("/terms/<int:user_id>")
def transaction_form(user_id):

    user = User.query.get(user_id)
    transactions = Transaction.query.filter(Transaction.payer_id == user_id).all()
    return render_template("transaction-form.html", user=user, transactions=transactions)


@app.route("/terms/<int:user_id>", methods=['POST'])
def approval_process(user_id):
    """Process approval."""

    # Get form variables
    seller_email = request.form.get("seller_email")
    seller_name = request.form.get("seller_name")
    date = request.form.get("date")
    amount = request.form.get("amount")
    currency = request.form.get("currency")

    date = datetime.datetime.strptime(date, "%Y-%m-%d")

    # The recipient is added to the database
    new_seller = User(fullname=seller_name, email=seller_email, password=0000, payer_seller="Seller")
    
    # At this point an email is sent to the seller to log in and view the contract"""

    db.session.add(new_seller)
    db.session.commit()

    seller = User.query.filter_by(email=seller_email).first()
    seller_id = seller.user_id

    # The new transaction is created in the database
    new_transaction = Transaction(payer_id=user_id,
                                  seller_id=seller_id,
                                  is_signed=False,
                                  payment_received=False,
                                  date=date,
                                  amount=amount,
                                  currency=currency,
                                  status="pending approval from seller")

    db.session.add(new_transaction)
    db.session.commit()

    user = User.query.get(user_id)

    flash("Approval prompt sent to the recipient")
    # return redirect("/homepage")
    return redirect("/homepage/%s" % user.user_id)
    # return "hello"


@app.route("/approved-form/<int:transaction_id>")
def show_approved_form(transaction_id):

    transaction = Transaction.query.get(transaction_id)
    user_id = session["user_id"]
    session["transaction"] = transaction_id
    return render_template('approved-contract.html', transaction=transaction, user_id=user_id)


@app.route('/payment')
def payment_form():

    return render_template('payment-form.html')


@app.route('/payment-processed', methods=['POST'])
def payment_process():

    """PROCESS FOR SELLER"""

    """Creates customer account and sends an email to the email automatically"""
    # seller = stripe.Account.create(
    #     country="US",
    #     managed=False,
    #     email='rayhanaziai@gmail.com'
    # )
    # """add this to database"""
    # seller = seller.to_dict()
    # account_number = seller["id"]
    # seller_keys = seller["keys"]
    # seller_keys = seller_keys.to_dict()
    # seller_s_key = seller_keys["secret"]


    # create_seller = stripe.Customer.create (
    #     email='jdg9843@gmail.com',
    #     api_key=seller_s_key
    # )



    token = request.form.get("stripeToken")
    # customer = stripe.Customer.create(
    #     email="buyertest@example.com",
    #     source=token,
    # )

    # requests.post
    # charge = stripe.Charge.create(
    #     amount=1000,
    #     currency="usd",
    #     customer=customer.id,
    # )

    print "***the token is", token

    return render_template('token-created.html')

@app.route('/seller-transfer', methods=['POST'])
def spayment_process():

    trnsfer = stripe.Transfer.create(
        amount=4200,
        currency='usd',
        source_transaction='id from charge',
        destination='pull this from database'
    )   

# @app.route('/stripe')
# def stripe_connect():

#     return render_template('stripe-connect.html')

# @app.route('/payment-paypal')
# def payment_form():

#     return render_template ('payment-form-paypal.html')


# @app.route('/payment-processed')
# def payment_processing():

#     paypalrestsdk.configure({
#         "mode": "sandbox",
#         "client_id": os.environ.get('CLIENT_ID'),
#         "client_secret": os.environ.get('CLIENT_SECRET')})

#     cardtype = request.form.get("cardtype")
#     cardnumber = request.form.get("cardnumber")
#     expirymonth = request.form.get("expirymonth")
#     expiryyear = request.form.get("expiryyear")
#     cvv = request.form.get("cvv")

#     payment = paypalrestsdk.Payment({
#        "intent": "sale",
#        "payer": {
#          "payment_method": "credit_card",
#          "funding_instruments": [{
#            "credit_card": {
#              "type": "amex",
#              "number": "371786672501009",
#              "expire_month": "07",
#              "expire_year": "2021",
#              "cvv2": "4117",
#              "first_name": "Rayhaneh",
#              "last_name": "Ziai" }}]},
#        "transactions": [{
#          "item_list": {
#            "items": [{
#              "name": "item",
#              "sku": "item",
#              "price": "1.00",
#              "currency": "USD",
#              "quantity": 1 }]},
#          "amount": {
#            "total": "1.00",
#            "currency": "USD"},
#          "description": "This is the payment transaction description."}]})

#     if payment.create():
#         print("Payment created successfully")
#     else:
#         print(payment.error)






    # data = {"grant_type":"client_credentials"}

    # headers = {"Content-Type": "application/x-www-form-urlencoded",
    #             "Authorization": "Basic QWZpWEhaUWM1U0R4d2RMNlBoNmY2RVpacFZXcVlmcnVRWDdqRkJDLU4xTngwNVYzY0RKNm9sbzNJRGlZaVVrbmowRXhnMWVCeE04WDhRemY6RUFyR294dnNsUmxtRElJaWdEWlloWWZtVUJxaWt4eW5HTnpfckd6c29qTDYzanZnNFZXOUFOVUJWb3l4QmZPZUp2SVlNbzZjU2J4TjY5dHg="}
    # r = requests.post('https://api.sandbox.paypal.com/v1/oauth2/token', headers=headers, params=data)
    # token = r.json().get("access_token")
    # print 'TOKEN:', token

    # return render_template('confirm-payment.html')


@app.route('/status')
def confirm_payment():

    return render_template('status.html')





if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(host="0.0.0.0")


