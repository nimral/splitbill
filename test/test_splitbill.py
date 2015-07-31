import unittest
from splitbill import settle
import pandas as pd


def bills(s):
    records = (x.split(",") for x in s.split("\n"))
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

        self.assertEqual(r, [("David", "John", 15)])
