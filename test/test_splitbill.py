import unittest
from splitbill import settle
import pandas as pd


def bills(s):
    records = ([y.strip() for y in x.split(",")] for x in s.split("\n"))
    columns = ["Name", "What", "Amount", "Currency", "For"]
    df = pd.DataFrame.from_records(records, columns=columns)
    df["Amount"] = df["Amount"].map(float)
    df["For"] = df["For"].map(str.split)
    return df


class TestSettle(unittest.TestCase):
    """Test if everybody gets the money he should."""

    def test_one_debt(self):
        exchange_rates = {"CZK": 1}

        df = bills("John,Icecream,15,CZK,David")
        r = settle(["John", "David"], exchange_rates, df)

        self.assertEqual(r, {("David", "John", 15)})


    def test_mutual_debts(self):
        exchange_rates = {"CZK": 1}

        df = bills("""John,Icecream,20,CZK,David
                      David,Kofola,20,CZK,John""")
        r = settle(["John", "David"], exchange_rates, df)

        self.assertEqual(r, set())

    
    def test_circular_debts(self):
        exchange_rates = {"CZK": 1}

        df = bills("""John,Item,10,CZK,David
                      David,Item,10,CZK,Martin
                      Martin,Item,10,CZK,John""")
                    
        r = settle(["John", "David", "Martin"], exchange_rates, df)

        self.assertEqual(r, set())


    def test_circular_debts_one_bigger(self):
        exchange_rates = {"CZK": 1}

        df = bills("""John,Item,10,CZK,David
                      David,Item,10,CZK,Martin
                      Martin,Item,10,CZK,Adam
                      Adam,Item,11,CZK,John""")
                    
        r = settle(["John", "David", "Martin", "Adam"], exchange_rates, df)

        self.assertEqual(r, {("John", "Adam", 1)})


    def test_shared_debt(self):
        exchange_rates = {"CZK": 1}

        df = bills("""Jan,Ticket,1400,CZK,Matěj Petr""")

        r = settle(["Jan", "Petr", "Matěj"], exchange_rates, df)

        self.assertEqual(r, {("Petr", "Jan", 700), ("Matěj", "Jan", 700)})

