from jinja2 import StrictUndefined

from flask import Flask, render_template, request, flash, redirect, session
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db
import urllib
import requests
import os
import paypalrestsdk
import stripe
import json

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
    country = request.form.get("country")

    # new_user = User(email=email, password=password, age=age, zipcode=zipcode)

    # db.session.add(new_user)
    # db.session.commit()

    # flash("User %s added." % email)
    return redirect("/")

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

    # user = User.query.filter_by(email=email).first()

    # if not user:
    #     flash("No such user")
    #     return redirect("/login")

    # if user.password != password:
    #     flash("Incorrect password")
    #     return redirect("/login")

    # session["user_id"] = user.user_id

    # flash("Logged in")
    # return redirect("/users/%s" % user.user_id)


@app.route('/logout')
def logout():
    """Log out."""

    del session["user_id"]
    flash("Logged Out.")
    return redirect("/")


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


