from jinja2 import StrictUndefined

from flask import Flask, render_template, request, flash, redirect, session
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db
import urllib
import requests
import os 

app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "MYSECRETKEY"

# Normally, if you use an undefined variable in Jinja2, it fails silently.
# This is horrible. Fix this so that, instead, it raises an error.
app.jinja_env.undefined = StrictUndefined


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


@app.route('/payment')
def payment_form():

    return render_template('payment-form.html')


@app.route('/payment-processed', methods=['POST'])
def payment_process():

    token = request.form.get("stripeToken")
    print "***the token is", token

    return render_template('token-created.html')


@app.route('/stripe')
def stripe_connect():

    return render_template('stripe-connect.html')


@app.route('/confirm-payment')
def show_status():

    code = request.args.get("code")
    data = {"grant_type": "authorization_code",
            "client_id": 'ca_A4Vr96Npe5T3IVSo4B9JemS3oN4b2y8I',
            "client_secret": 'sk_test_uXpQmqM8CWnoWDgkKQJUFcDZ',
            "code": code
            }
    r = requests.post('https://connect.stripe.com/oauth/token', params=data)
    token = r.json().get('access_token')
    print "****THE TOKEN****", token

    return render_template('confirm-payment.html', token=token)

@app.route('/status')
def confirm_payment():

    render_template

if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(host="0.0.0.0")


