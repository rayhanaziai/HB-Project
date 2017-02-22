from jinja2 import StrictUndefined
from flask import Flask, render_template, request, flash, redirect, session, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from model import connect_to_db, db, User, Transaction
import requests
import stripe
import json
import datetime
import os
# from sqlalchemy.exc import InvalidRequestError

app = Flask(__name__)
# Required to use Flask sessions and the debug toolbar
app.secret_key = "MYSECRETKEY"

# Normally, if you use an undefined variable in Jinja2, it fails silently.
# This is horrible. Fix this so that, instead, it raises an error.
app.jinja_env.undefined = StrictUndefined

# stripe.api_key = "sk_test_uXpQmqM8CWnoWDgkKQJUFcDZ"
stripe.api_key = os.environ['STRIPE_KEY']

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
    if User.query.filter_by(email=email).all() == []:
        current_user = User(fullname=fullname,
                            email=email,
                            password=password,
                            payer_seller=payer_seller)
        db.session.add(current_user)
    else:
        current_user = User.query.filter_by(email=email).first()
        current_user.fullname = fullname
        current_user.password = password
        current_user.payer_seller = payer_seller

    db.session.commit()

    flash("User %s added." % fullname)

    session["user_id"] = current_user.user_id
    session["payer_seller"] = current_user.payer_seller
    return redirect("/homepage/%s" % current_user.user_id)


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
    del session["payer_seller"]
    flash("Logged Out.")
    return redirect("/")


@app.route("/homepage/<int:user_id>", methods=['GET'])
def status(user_id):
    """Show info about user."""

    user_id = session["user_id"]
    user = User.query.get(user_id)
    print "payer_seller", user.payer_seller

    if user.payer_seller == "Payer":
        transaction_filter = Transaction.payer_id == user_id
    else:
        transaction_filter = Transaction.seller_id == user_id

    transactions = Transaction.query.filter(transaction_filter).all()

    completed_transactions = Transaction.query.filter(
        transaction_filter, Transaction.status == "completed").all()

    pending_transactions = Transaction.query.filter(
        transaction_filter, Transaction.status != "completed").all()

    print "Pending:", pending_transactions

    return render_template("userpage.html",
                           user=user,
                           completed_transactions=completed_transactions,
                           pending_transactions=pending_transactions)


@app.route("/homepage/<int:user_id>", methods=['POST'])
def process_acceptance(user_id):
    """Change status of transaction depending on seller acceptance"""

    acceptance = request.form.get("agree_or_disagree")

    transaction_id = session["transaction"]
    current_transaction = Transaction.query.get(transaction_id)
    seller_user = User.query.get(user_id)
    payer_user = User.query.get(current_transaction.payer_id)

    if acceptance == "agree":
        current_transaction.status = "awaiting payment from payer"
        html = "<html><h2>Easy Pay</h2><br><p>Hi " + payer_user.fullname + ",</p><br>" + seller_user.fullname + " has approved your contract. Please<a href='http://localhost:5000/login'><span> log in </span></a>to make your payment to Easy Pay.<br><br> From the Easy Pay team!</html>"

        requests.post(
            "https://api.mailgun.net/v3/sandbox9ba71cb39eb046f798ee4676ad972946.mailgun.org/messages",
            auth=('api', 'key-fcaee27772f7acfa5b4246ae675248a0'),
            data={"from": "rayhana.z@hotmail.com",
                  "to": payer_user.email,
                  "subject": "Contract approved!",
                  "text": "Hi, Please sign into easy pay to view the contract and get paid",
                  "html": html})

    else:
        current_transaction.status = "declined by seller"
    db.session.commit()

    # At this stage an email is sent to the buyer with prompt to pay.
    return redirect("/homepage/%s" % user_id)


@app.route("/terms/<int:user_id>")
def transaction_form(user_id):

    user = User.query.get(user_id)
    return render_template("transaction-form.html", user=user)


# @app.route("/terms/<int:user_id>", methods=['POST'])
# def approval_process(user_id):
#     """Process approval."""

#     # Get form variables
#     seller_email = request.form.get("seller_email")
#     seller_name = request.form.get("seller_name")
#     date = request.form.get("date")
#     amount = request.form.get("amount")
#     currency = request.form.get("currency")

#     date = datetime.datetime.strptime(date, "%Y-%m-%d")

#     # The recipient is added to the database
#     # password = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
#     password = 0000
#     if User.query.filter_by(email=seller_email).all() == []:
#         new_seller = User(fullname=seller_name, email=seller_email, password=password, payer_seller="Seller")
#         db.session.add(new_seller)
#     else:
#         User.query.filter_by(email=seller_email).first().payer_seller = "Seller"

#     db.session.commit()

#     seller = User.query.filter_by(email=seller_email).first()
#     seller_id = seller.user_id
#     payer_id = session['user_id']
#     payer = User.query.get(payer_id)
#     payer_name = payer.fullname
#     # An email is sent to the seller to log in and view the contract

#     html = "<html><h2>Easy Pay</h2><br><p>Hi " + seller_name + ",</p><br>" + payer_name + " would like to send you money via Easy Pay. <br> Please<a href='http://localhost:5000/login'><span> log in </span></a> to view and accept the contract:<br>Password: " + str(password) + "<br><br> From the Easy Pay team!</html>"

#     requests.post(
#         "https://api.mailgun.net/v3/sandbox9ba71cb39eb046f798ee4676ad972946.mailgun.org/messages",
#         auth=('api', 'key-fcaee27772f7acfa5b4246ae675248a0'),
#         data={"from": "rayhana.z@hotmail.com",
#               "to": seller_email,
#               "subject": "Log in to Easy Pay",
#               "text": "Hi, Please sign into easy pay to view the contract and get paid",
#               "html": html})

#     # The new transaction is created in the database
#     new_transaction = Transaction(payer_id=user_id,
#                                   seller_id=seller_id,
#                                   is_signed=False,
#                                   payment_received=False,
#                                   date=date,
#                                   amount=amount,
#                                   currency=currency,
#                                   status="pending approval from seller")

#     db.session.add(new_transaction)
#     db.session.commit()


#     flash("Approval prompt sent to the recipient")
#     # return redirect("/homepage")
#     return redirect("/homepage/%s" % payer_id)
    # return "hello"


@app.route("/terms.json", methods=['POST'])
def approval_process():
    """Process approval."""

    # Get form variables
    seller_email = request.form.get("seller_email")
    seller_name = request.form.get("seller_name")
    date = request.form.get("date")
    amount = request.form.get("amount")
    currency = request.form.get("currency")

    date = datetime.datetime.strptime(date, "%Y-%m-%d")

    # The recipient is added to the database
    # password = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    password = 0000
    if User.query.filter_by(email=seller_email).all() == []:
        new_seller = User(fullname=seller_name, email=seller_email, password=password, payer_seller="Seller")
        db.session.add(new_seller)
    else:
        User.query.filter_by(email=seller_email).first().payer_seller = "Seller"

    db.session.commit()

    seller = User.query.filter_by(email=seller_email).first()
    seller_id = seller.user_id
    payer_id = session['user_id']
    payer = User.query.get(payer_id)
    payer_name = payer.fullname
    # An email is sent to the seller to log in and view the contract

    html = "<html><h2>Easy Pay</h2><br><p>Hi " + seller_name + ",</p><br>" + payer_name + " would like to send you money via Easy Pay. <br> Please<a href='http://localhost:5000/login'><span> log in </span></a> to view and accept the contract:<br>Password: " + str(password) + "<br><br> From the Easy Pay team!</html>"

    requests.post(
        "https://api.mailgun.net/v3/sandbox9ba71cb39eb046f798ee4676ad972946.mailgun.org/messages",
        auth=('api', 'key-fcaee27772f7acfa5b4246ae675248a0'),
        data={"from": "rayhana.z@hotmail.com",
              "to": seller_email,
              "subject": "Log in to Easy Pay",
              "text": "Hi, Please sign into easy pay to view the contract and get paid",
              "html": html})

    # The new transaction is created in the database
    new_transaction = Transaction(payer_id=payer_id,
                                  seller_id=seller_id,
                                  is_signed=False,
                                  payment_received=False,
                                  date=date,
                                  amount=amount,
                                  currency=currency,
                                  status="pending approval from seller")

    db.session.add(new_transaction)
    db.session.commit()

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

    transaction = Transaction.query.get(transaction_id)
    user_id = session["user_id"]
    payer_seller = session["payer_seller"]
    session["transaction"] = transaction_id
    return render_template('approved-contract.html', transaction=transaction, user_id=user_id, payer_seller=payer_seller)


@app.route('/payment/<int:transaction_id>')
def payment_form(transaction_id):

    return render_template('payment-form.html', transaction_id=transaction_id)


@app.route('/payment/<int:transaction_id>', methods=['POST'])
def payment_process(transaction_id):

    token = request.form.get("stripeToken")

    transfer = Transaction.query.get(transaction_id)
    payer_id = transfer.payer_id
    seller_id = transfer.seller_id
    seller_email = User.query.get(seller_id).email
    amount = transfer.amount*100
    currency = transfer.currency
    date = transfer.date
    description = "payment from %d to %d" % (payer_id, seller_id)

    # Any way to check if this payment causes error?
    charge = stripe.Charge.create(
        amount=amount,
        currency=currency,
        source=token,
        description=description
        )

    charge_id = charge.to_dict()['id']
    if charge.to_dict()['paid'] != True:
        flash("Your payment has not gone through. Please try again.")
    else:
        transfer.status = "payment to seller scheduled"
        db.session.commit()

        # As soon as payment is successfull, stripe account set up for seller.
        try:
            create_account = stripe.Account.create(
                country="US",
                managed=True,
                email=seller_email
                )

            account_id = create_account.to_dict()['id']
            s_key = create_account.to_dict()['keys']['secret']

            # Add account_id and s_key to database
            User.query.get(seller_id).account_id = account_id
            User.query.get(seller_id).secret_key = s_key

            db.session.commit()

            stripe.Customer.create(
                email=seller_email,
                api_key=s_key)

            stripe.Transfer.create(
                amount=amount,
                currency=currency,
                destination=account_id,
                description=description)

        except stripe.InvalidRequestError as e:
            flash(e.message)
            # send email to seller telling them to put their details in stripe

    print "***the token is", token
    return redirect("/homepage/%s" % (payer_id))



if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(host="0.0.0.0")


