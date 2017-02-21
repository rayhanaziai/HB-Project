from flask import Flask
from model import User, connect_to_db, db
from datetime import datetime


def make_new_user():
    """ """
    new_user = User(fullname='crontab2',
                    email="test@test2.com",
                    password=0,
                    payer_seller="Payer")

    db.session.add(new_user)
    db.session.commit()


if __name__ == "__main__":

    from server_2 import app
    # app = Flask(__name__)
    connect_to_db(app)
    print "Connected to DB."

    make_new_user()