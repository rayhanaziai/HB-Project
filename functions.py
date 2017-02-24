from model import db, User, Transaction
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def fetch_user(user_id):

    return User.query.get(user_id)


def user_by_email(email):

    return User.query.filter_by(email=email).first()


def add_user(name, email, password, payer_seller):
    current_user = User(fullname=fullname,
                        email=email,
                        password=password,
                        payer_seller=payer_seller)
    db.session.add(current_user)
    db.session.commit()

def fetch_trans(transaction_id):

    return Transaction.query.get(user_id)


