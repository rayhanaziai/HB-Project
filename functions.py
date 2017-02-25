from model import db, User, Transaction
from flask_sqlalchemy import SQLAlchemy
import stripe


def fetch_user(user_id):

    return User.query.get(user_id)


def user_by_email(email):

    return User.query.filter_by(email=email).first()


def add_user(name, email, password, payer_seller):
    new_user = User(fullname=fullname,
                    email=email,
                    password=password,
                    payer_seller=payer_seller)

    db.session.add(new_user)
    db.session.commit()


def fetch_trans(transaction_id):

    return Transaction.query.get(user_id)


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


def create_cust_token(name, routing_number, account_number):

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
