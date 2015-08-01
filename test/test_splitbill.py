import unittest
from splitbill import settle
import pandas as pd


def bills(s):
    """Create pd.DataFrame with bills from csv string."""

    records = ([y.strip() for y in x.split(",")] for x in s.split("\n"))
    columns = ["Name", "What", "Amount", "Currency", "For"]
    df = pd.DataFrame.from_records(records, columns=columns)
    df["Amount"] = df["Amount"].map(float)
    df["For"] = df["For"].map(str.split)
    return df


def will_get(name, payments):
    """Calculate how much money will a person 'name' get from payments."""

    r = 0
    r += sum(p for who, whom, p in payments if whom == name)
    r -= sum(p for who, whom, p in payments if who == name)
    return r


class TestSettle(unittest.TestCase):
    """Test if everybody gets the money he should."""

    def test_one_debt(self):
        """Lender should get his money back."""

        exchange_rates = {"CZK": 1}

        df = bills("John,Icecream,15,CZK,David")
        r = settle(["John", "David"], exchange_rates, df)

        self.assertEqual(r, {("David", "John", 15)})


    def test_mutual_debts(self):
        """If a owes b and b owes a the same amount, no payments are needed."""

        exchange_rates = {"CZK": 1}

        df = bills("""John,Icecream,20,CZK,David
                      David,Kofola,20,CZK,John""")
        r = settle(["John", "David"], exchange_rates, df)

        self.assertEqual(r, set())


    def test_circular_debts(self):
        """In case of circular debts of the same value, no payments are needed.
        """

        exchange_rates = {"CZK": 1}

        df = bills("""John,Item,10,CZK,David
                      David,Item,10,CZK,Martin
                      Martin,Item,10,CZK,John""")

        r = settle(["John", "David", "Martin"], exchange_rates, df)

        self.assertEqual(r, set())


    def test_circular_debts_one_bigger(self):
        """Only the amount owed above level of circular debts should be paid.
        """

        exchange_rates = {"CZK": 1}

        df = bills("""John,Item,10,CZK,David
                      David,Item,10,CZK,Martin
                      Martin,Item,10,CZK,Adam
                      Adam,Item,11,CZK,John""")

        r = settle(["John", "David", "Martin", "Adam"], exchange_rates, df)

        self.assertEqual(r, {("John", "Adam", 1)})


    def test_shared_debt(self):
        """If a thing was bought for several people, they should all pay for it
        """

        exchange_rates = {"CZK": 1}

        df = bills("""Jan,Ticket,1400,CZK,Matěj Petr""")
        r = settle(["Jan", "Petr", "Matěj"], exchange_rates, df)
        self.assertEqual(r, {("Petr", "Jan", 700), ("Matěj", "Jan", 700)})

        df = bills("""Jan,Ticket,1500,CZK,Matěj Petr Martin""")
        r = settle(["Jan", "Petr", "Matěj", "Martin"], exchange_rates, df)
        self.assertEqual(r, {
                             ("Petr", "Jan", 500),
                             ("Matěj", "Jan", 500),
                             ("Martin", "Jan", 500),
                            })

        df = bills("""Jan,Ticket,1500,CZK,AllBut Jan""")
        r = settle(["Jan", "Petr", "Matěj", "Martin"], exchange_rates, df)
        self.assertEqual(r, {
                             ("Petr", "Jan", 500),
                             ("Matěj", "Jan", 500),
                             ("Martin", "Jan", 500),
                            })


    def test_all_shortcut(self):
        """Test if using All instead of all the names gives the same result
        """

        exchange_rates = {"CZK": 1}

        people = ["Jan", "Matěj", "Petr", "Martin"]

        df1 = bills("""Petr,Accomodation,395,CZK,Jan Matěj Petr Martin""")
        df2 = bills("""Petr,Accomodation,395,CZK,All""")

        r1 = settle(people, exchange_rates, df1)
        r2 = settle(people, exchange_rates, df2)

        self.assertEqual(r1, r2)


    def test_allbut_shortcut(self):
        """Test if using AllBut instead of rest of names gives the same result.
        """

        exchange_rates = {"CZK": 1}

        people = ["Jan", "Matěj", "Petr", "Martin"]

        df1 = bills("""Jan,Ticket,1200,CZK,Matěj Petr Martin""")
        df2 = bills("""Jan,Ticket,1200,CZK,AllBut Jan""")

        r1 = settle(people, exchange_rates, df1)
        r2 = settle(people, exchange_rates, df2)

        self.assertEqual(r1, r2)


    def test_more_currencies(self):
        """Test if bills in different currencies are counted right."""

        exchange_rates = {"CZK": 1, "EUR": 30, "USD": 20}


        df = bills("""John,Lunch,100,CZK,David
                      David,Dinner,2,EUR,John
                      Adam,Breakfast,1,USD,John""")

        r = settle(["John", "David", "Adam"], exchange_rates, df)

        self.assertEqual(will_get("John", r), 20)
        self.assertEqual(will_get("David", r), -40)
        self.assertEqual(will_get("Adam", r), 20)


    def test_requires_exchange_rate(self):
        """Does settle raise exception if supplied bill with unknown currency?
        """

        exchange_rates = {"CZK": 1}

        df = bills("""John,Item,100,CZK,David
                      David,Item,2,EUR,John""")
        people = ["John", "David"]

        self.assertRaises(ValueError, settle, people, exchange_rates, df)
