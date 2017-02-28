import unittest
from model import db, connect_to_db, User, Transaction
from server_2 import app
from datetime import datetime

######################################################################
# Tests that don't require the database or an active session
######################################################################

class EasyPayTests(unittest.TestCase):
    """Tests for my easypay site."""

    def setUp(self):
        self.client = app.test_client()
        app.config['TESTING'] = True

    def test_homepage(self):
        result = self.client.get("/")
        self.assertIn("Uneasy about sending money online", result.data)

    def test_login_page(self):
        result = self.client.get("/login")
        self.assertIn("Login", result.data)

    def test_register_page(self):
        result = self.client.get("/register")
        self.assertIn("Full name:", result.data)

    # def test_rsvp(self):
    #     result = self.client.post("/rsvp",
    #                               data={'name': "Jane", 'email': "jane@jane.com"},
    #                               follow_redirects=True)
    #     self.assertIn("Yay!", result.data)
    #     self.assertIn("Party Details", result.data)
    #     self.assertNotIn("Please RSVP", result.data)

######################################################################
# Tests that require an active session, but no database access
######################################################################


class EasyPaySessionTests(unittest.TestCase):
    """Tests that require the session to be active but do not interact
    with the database."""

    def setUp(self):
        self.client = app.test_client()
        app.config['TESTING'] = True

        add_test_user_to_session(self.client)

    def test_logout(self):
        add_test_user_to_session(self.client)

        result = self.client.get("/logout", follow_redirects=True)
        self.assertIn("Uneasy about sending money online", result.data)

######################################################################
# Tests that require database access but not an active session. These
# should not be able to change the database.
######################################################################


class EasyPayQueriesTestsNoSessionTests(unittest.TestCase):
    """Tests that query the database but don't require a session."""

    def setUp(self):
        """Necessary before every test. Creates client, configures the app,
        connects to test database, creates the tables, and seeds the test database."""

        self.client = app.test_client()
        app.config['TESTING'] = True

        connect_to_db(app, "postgresql:///testdb")

        db.create_all()
        example_data()

    def tearDown(self):
        """Do at the end of every test"""

        db.session.close()
        db.drop_all()

######################################################################
# Tests that require database access and an active session, but don't
# alter the state of the database.
######################################################################

class EasyPayQueriesAndSessionTests(unittest.TestCase):
    """Tests that query the database and require a session, but don't alter the
    database."""

    def setUp(self):
        """Necessary before every test. Creates client, configures the app, 
        connects to test database, creates the tables, and seeds the test database."""

        self.client = app.test_client()
        app.config['TESTING'] = True

        connect_to_db(app, "postgresql:///testdb")

        db.create_all()
        example_data()

        add_test_user_to_session(self.client)

    def tearDown(self):
        """Do at the end of every test"""

        db.session.close()
        db.drop_all()

    def test_login(self):
        result = self.client.post("/login",
                                  data={"email": "fake@email.com",
                                        "password": "secretpassword"},
                                        follow_redirects=True)

        self.assertIn("Welcome, Jess", result.data)

    def test_show_boards(self):
        """Test that boards are displaying on user homepage"""

        result = self.client.get("/users/1")
        self.assertIn("My Board", result.data)
        self.assertNotIn("Log In", result.data)

    def test_new_board(self):
        """Test ability to get to new board page"""

        result = self.client.get("/create-board")
        self.assertIn("New Board", result.data)
        self.assertNotIn("Welcome", result.data)

    def test_board_display(self):
        """Test squares displaying on board"""

        result = self.client.get("/board/1")
        self.assertIn("Romance", result.data)
        self.assertNotIn("Welcome", result.data)

######################################################################
# Example data to test database
######################################################################

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


    new_trans = Transaction(payer_id=1,
                            seller_id=2,
                            is_signed=False,
                            payment_received=False,
                            date=datetime(2017, 06, 06, 0, 0),
                            amount=1000,
                            currency='usd',
                            status='pending approval from seller')

    new_trans = Transaction(payer_id=3,
                            seller_id=4,
                            is_signed=False,
                            payment_received=False,
                            date=datetime(2017, 11, 11, 0, 0),
                            amount=1000,
                            currency='usd',
                            status='pending approval from seller')

    board1 = Board(board_name="My Board")
    board2 = Board(board_name="Bingo 2017")

    board1.users.append(u1)
    board1.users.append(u2)

    book1 = Book(title="Pride and Prejudice", author="Jane Austen")
    book2 = Book(title="Mort", author="Terry Pratchett")

    genre1 = Genre(name="Romance")
    genre2 = Genre(name="Fantasy")

    book1.genres.append(genre1)
    book2.genres.append(genre2)

    square1 = Square(x_coord=1, y_coord=1)
    square2 = Square(x_coord=1, y_coord=2)


    board1.squares.append(square1)
    board1.squares.append(square2)

    square1.genre = genre1
    square2.genre = genre2

    su1 = SquareUser()
    su2 = SquareUser()

    su1.user = u1
    su1.square = square1
    su1.book = book1

    su2.user = u2
    su2.square = square2
    su2.book = book2

    db.session.add_all([su1, su2])
    db.session.commit()

######################################################################
# Helper functions to run the tests
######################################################################


def add_test_user_to_session(client):
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['payer_seller'] = 'Payer'


if __name__ == "__main__":
    unittest.main()

