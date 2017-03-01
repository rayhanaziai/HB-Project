from model import db, User, Transaction
from flask_sqlalchemy import SQLAlchemy
import stripe


def fetch_user(user_id):

    return User.query.get(user_id)


def user_by_email(email):

    return User.query.filter_by(email=email).first()


def add_user(fullname, email, password, payer_seller):
    new_user = User(fullname=fullname,
                    email=email,
                    password=password,
                    payer_seller=payer_seller)

    db.session.add(new_user)
    db.session.commit()

    return new_user


def fetch_trans(transaction_id):

    return Transaction.query.get(transaction_id)


def add_trans(payer_id, seller_id, is_signed, payment_received, date, amount, currency, status):
    new_trans = Transaction(payer_id=payer_id,
                            seller_id=seller_id,
                            is_signed=is_signed,
                            payment_received=payment_received,
                            date=date,
                            amount=amount,
                            currency=currency,
                            status=status)
    db.session.add(new_trans)
    db.session.commit()
    return new_trans


def new_status(transaction_id, new):

    Transaction.query.get(transaction_id).status = new
    db.session.commit()


def create_charge(amount, token, description):

    return stripe.Charge.create(
        amount=amount,
        currency='usd',
        source=token,
        description=description
        )


def create_seller_account(currency, email):

    return stripe.Account.create(
        country='us',
        managed=True,
        email=email
        )


def create_seller_token(name, routing_number, account_number):

    response = stripe.Token.create(
        bank_account={
            "country": 'US',
            "currency": 'usd',
            "account_holder_name": name,
            "account_holder_type": 'individual',
            "routing_number": routing_number,
            "account_number": account_number
            },
        )
    return response


def create_customer(email, api_key):

    return stripe.Customer.create(email=email,
                                  api_key=api_key)


def create_transfer(amount, currency, destination):

    # source=account_token would be added at deployment
    # destination is always the account_id
    return stripe.Transfer.create(amount=amount,
                           currency=currency,
                           destination=destination)
