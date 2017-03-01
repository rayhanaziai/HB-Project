from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


#####################################################################
# Model definitions

class User(db.Model):
    """User of ratings website."""

    __tablename__ = "users"

    user_id = db.Column(db.Integer,
                        autoincrement=True,
                        primary_key=True)
    fullname = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(64), nullable=False)
    account_id = db.Column(db.String(300), nullable=True)
    secret_key = db.Column(db.String(300), nullable=True)
    payer_seller = db.Column(db.String(20), nullable=False)

    # transaction = db.relationship("Transaction",
    #                               backref=db.backref("users", order_by=user_id))
    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<User user_id=%s email=%s>" % (self.user_id,
                                               self.email)

    @classmethod
    def fetch(cls, user_id):
        return cls.query.get(user_id)


class Transaction(db.Model):
    """Movie on ratings website."""

    __tablename__ = "transactions"

    transaction_id = db.Column(db.Integer,
                               autoincrement=True,
                               primary_key=True)
    payer_id = db.Column(db.Integer,
                         db.ForeignKey('users.user_id'))
    seller_id = db.Column(db.Integer,
                          db.ForeignKey('users.user_id'))
    charge_id = db.Column(db.String(300), nullable=True)
    is_signed = db.Column(db.Boolean, nullable=False)
    payment_received = db.Column(db.Boolean, nullable=True)
    date = db.Column(db.DateTime, nullable=True)
    amount = db.Column(db.Integer, nullable=True)
    currency = db.Column(db.String(3), nullable=True)
    status = db.Column(db.String(50), nullable=False)

    payer = db.relationship("User", foreign_keys=[payer_id])
    seller = db.relationship("User", foreign_keys=[seller_id])


    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<Transaction transaction_id=%s is_signed=%s>" % (self.transaction_id,
                                                                 self.is_signed)


#####################################################################
# Helper functions

def connect_to_db(app, database_uri):
    """Connect the database to our Flask app."""

    # Configure to use our PostgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    db.app = app
    db.init_app(app)

def example_data():
    """Create example data to test the database"""

    u1 = User(fullname="Test Person",
              email="testperson@test.com",
              password='0000',
              payer_seller="Payer")

    u2 = User(fullname="Test Person2",
              email="testperson2@test.com",
              password='0000',
              account_id='acct_19rvdXFByeZDKBFc',
              secret_key='sk_test_FMu4VqVNvb1oqZAWYTBh3kvj',
              payer_seller="Seller")

    u3 = User(fullname="Test Person3",
              email="testperson3@test.com",
              password='0000',
              payer_seller="Payer")

    u4 = User(fullname="Test Person4",
              email="testperson4@test.com",
              account_id='acct_19rvdXFByeZDKBFc',
              secret_key='sk_test_FMu4VqVNvb1oqZAWYTBh3kvj',
              password='0000',
              payer_seller="Seller")

    new_trans1 = Transaction(payer_id=1,
                             seller_id=2,
                             is_signed=False,
                             payment_received=False,
                             date=datetime(2017, 06, 06, 0, 0),
                             amount=1000,
                             currency='usd',
                             status='pending approval from seller')

    new_trans2 = Transaction(payer_id=3,
                             seller_id=4,
                             is_signed=False,
                             payment_received=False,
                             date=datetime(2017, 11, 11, 0, 0),
                             amount=1000,
                             currency='usd',
                             status='pending approval from seller')


    db.session.add_all([u1, u2, u3, u4, new_trans1, new_trans2])
    db.session.commit()



if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will
    # leave you in a state of being able to work with the database
    # directly.

    from server_2 import app
    connect_to_db(app, "postgresql:///easypay")
    print "Connected to DB."

