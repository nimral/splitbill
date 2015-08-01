import pandas as pd
import argparse


def settle(people, rates, bills, decimal_places=2):
    """Calculate the smallest set of transactions needed to settle debts.

    For each person we sum the money spent for her and subtract the money she
    paid. We get the amount she should pay (it does not matter to whom from her
    point of view). After she does, she should get 0 and pay 0, therefore she
    is solved. The person who got her money now should pay more (or get less).
    So in each step we choose one yet unsolved person, give the money she
    should pay to someone else who has not been solved yet and update the money
    he is due. In n-1 steps we settle all debts (n is the number of people).

    Arguments

    people: list of strings - names of all the people. (Needed for All shortcut
        in csv)
    rates: dict of str -> float - exchange rates of currencies to the
        currency in which debts should be paid. Exchange rate for each currency
        (other than final_currency) that appears in filename should be
        specified.
    bills: pd.DataFrame - bills. Should have columns Name (of the person who
        paid), What (has been paid), Amount (of money paid), Currency (in which
        it has been paid; for example "EUR"), For (whom it has been paid;
        either ["All"] or list of names or ["AllBut"] + list of names, for
        example ["AllBut", "Adam", "David"]).
    decimal_places: int - number of decimal places to which the amounts to be
        paid should be rounded. Default 2.

    Return list of tuples (who:str, whom:str, how_much_should_pay:float)
    """

    df = bills.copy()

    # add column to df - amount of money in the final currency
    try:
        df["AmountInCUR"] = df.Currency.map(lambda x: rates[x]) * df.Amount
    except KeyError as k:
        raise ValueError("Exchange rate for %s not specified" % (k.args[0]))

    # add lines to df for each person paying nothing for all
    df_people = pd.DataFrame({
        "Name": people,
        "AmountInCUR": [0] * len(people),
        "For": ["All"] * len(people)
    })
    df = df.append(df_people)

    # dict {"person": money spent for her, regardless who paid}
    money_spent = {}
    for person in people:
        money_spent.setdefault(person, 0)
        for amount, fw in zip(df.AmountInCUR, df.For):
            if fw[0] == "All":
                money_spent[person] += amount / len(people)
            elif fw[0] == "AllBut" and person not in fw[1:]:
                money_spent[person] += amount / (len(people) - (len(fw)-1))
            elif fw[0] != "AllBut" and person in fw:
                money_spent[person] += amount / len(fw)

    # just creating pd.DataFrame from dict
    tmp = pd.DataFrame.from_records(list(money_spent.items()))
    tmp.columns = ["Name", "MoneySpent"]

    # create pd.DataFrame with columns "Name", "MoneySpent", "MoneyPaid",
    # "ShouldPay"; one row for each person
    sums = df.filter(["Name", "AmountInCUR"]).groupby("Name").sum()
    sums.columns = ["MoneyPaid"]
    sums = pd.merge(tmp, sums, left_on="Name", right_index=True)
    sums["ShouldPay"] = sums.MoneySpent - sums.MoneyPaid

    howto = sums.sort("ShouldPay")

    # set of tuples (who, whom, how_much_should_pay)
    payments = set()

    # topay - list of lists [how_much_should_pay, "who"]
    topay = [[p, w] for p, w in zip(howto.ShouldPay, howto.Name) if p != 0]

    # Keep people sorted by the amount of money they should pay.
    # At each step take all the money the last one in the list should pay (it
    # is the one who should pay most) and give it to the first one -> the last
    # one is solved and removed from the list.  Because the overall amount of
    # money that should be paid is equal to the overall amount of money that
    # should be received, in at most n-1 steps all the debts are settled (where
    # n is the number of people involved).

    while len(topay) > 1:
        pay, who = topay.pop()
        topay[0][0] += pay
        payments.add((who, topay[0][1], round(pay, decimal_places)))
        topay.sort()

    return set(payments)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Determines the least possible amount of transactions to "
                    "settle debts")
    parser.add_argument("-c", "--currency", default="CZK",
                        help="Currency in which the debts will be settled")
    parser.add_argument("-x", "--exchange-rates", default="",
                        help="Exchange rates in the form 'USD:20,EUR:27.09'")
    parser.add_argument("-p", "--people", required=True,
                        help="List of all the people involved, for example "
                        "'Adam,David'. Spaces in names not allowed.")
    parser.add_argument("-d", "--decimal_places", default=2,
                        help="Number of decimal places to which amounts "
                        "should be rounded.")
    parser.add_argument("file.csv")

    args = vars(parser.parse_args())

    # exchange rate for the final currency is 1:1
    exchange_rates = {args["currency"]: 1}

    for pair in args["exchange_rates"].split(","):
        if not pair:
            continue

        try:
            cur, rate_str = pair.split(":")
        except ValueError:
            raise ValueError("Bad format of exchange rate string:'{}' "
                             "Should be for example 'CUR:12.3'".format(pair))

        exchange_rates[cur] = float(rate_str)

    people = args["people"].split(",")

    df = pd.read_csv(args["file.csv"])
    df["For"] = df["For"].map(str.split)

    z = list(settle(people, exchange_rates, df, args["decimal_places"]))
    print(pd.DataFrame.from_records(z, columns=["Who", "ToWhom", "HowMuch"]))
