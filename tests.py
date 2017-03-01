import unittest
from datetime import datetime

from model import db, connect_to_db, User, Transaction, example_data

from server_2 import app

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
                                  data={"email": "testperson@test.com",
                                        "password": '0000'},
                                  follow_redirects=True)

        self.assertIn("Hi Test Person", result.data)

    def test_dashboard_tables(self):
        """Test that transactions are showing on the pending table"""

        result = self.client.get("/homepage")
        self.assertIn("pending approval from seller", result.data)
        self.assertNotIn("Log In", result.data)

    def test_payment(self):
        """Test ability to get to payment page"""

        result = self.client.get("/payment/1")
        self.assertIn("Card Number", result.data)
        self.assertNotIn("dashboard", result.data)

    def test_account_details(self):
        """Test ability to get to the account details page"""

        result = self.client.get("/accounts/1")
        self.assertIn("Routing Number", result.data)
        self.assertNotIn("dashboard", result.data)

######################################################################
# Tests that require database access, need an active session, and
# can actually change the database.
######################################################################

class EasyPayDBTests(unittest.TestCase):
    """Tests that alter the test database."""

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

    def test_registration(self):
        """Test registration process"""

        result = self.client.post("/register",
                                  data={'fullname': "John Smith",
                                        'email': "johnsmith@test.com",
                                        'password': "0000",
                                        "payer_or_receiver": "Payer"})

        self.assertEqual(result.status_code, 302)

    def test_create_transaction(self):
        """Test new transaction creation"""

        data = {'date': '2017-03-22',
                'amount': '1000',
                'currency': 'usd',
                'seller_name': 'Henny Ziai',
                'seller_email': 'henny.ziai@test.com'}

        result = self.client.post("/terms.json",
                                  data=data)

        self.assertEqual(result.status_code, 200)

######################################################################
# Helper functions to run the tests
######################################################################


def add_test_user_to_session(client):
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['payer_seller'] = 'Payer'


if __name__ == "__main__":
    unittest.main()
