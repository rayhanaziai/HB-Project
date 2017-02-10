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
    payer_receiver = db.Column(db.String(20), nullable=False)

    transactions = db.relationship("Transaction")

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<User user_id=%s email=%s>" % (self.user_id,
                                               self.email)


class Transaction(db.Model):
    """Movie on ratings website."""

    __tablename__ = "transactions"

    transaction_id = db.Column(db.Integer,
                               autoincrement=True,
                               primary_key=True)
    buyer_id = db.Column(db.String,
                         db.ForeignKey('users.user.id'))
    seller_id = db.Column(db.String,
                          db.ForeignKey('users.user.id'))
    charge_id = db.Column(db.String(300), nullable=True)
    is_signed = db.Column(db.Boolean, nullable=False)
    payment_recieved = db.Column(db.Boolean, nullable=True)
    date = db.Column(db.DateTime, nullable=True)
    amount = db.Column(db.Integer, nullable=True)
    currency = db.Column(db.String(3), nullable=True)

    users = db.relationship("User")

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<Transaction transaction_id=%s is_signed=%s>" % (self.transaction_id,
                                                                 self.is_signed)


#####################################################################
# Helper functions

def connect_to_db(app):
    """Connect the database to our Flask app."""

    # Configure to use our PostgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///easypay'
    db.app = app
    db.init_app(app)


if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will
    # leave you in a state of being able to work with the database
    # directly.

    from serverPP import app
    connect_to_db(app)
    print "Connected to DB."
