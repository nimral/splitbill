import pandas as pd
import argparse


def settle(people, exchange_rates, filename, decimal_places=2):
    """Calculate the smallest set of transactions needed to settle debts

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
    exchange_rates: dict of str -> float - exchange rates of currencies to the
        currency in which debts should be paid. Exchange rate for each currency
        (other than final_currency) that appears in filename should be
        specified.
    filename: string - name of csv file with accounts. The file should contain
        columns Name (of the person who paid), What (has been paid), Amount (of
        money paid), Currency (in which it has been paid; for example "EUR"),
        For (whom it has been paid; either "All" or space separated names or
        "AllBut " and space separated names, for example "AllBut Adam David").
    decimal_places: int - number of decimal places to which the amounts to be
        paid should be rounded. Default 2.

    Returns list of tuples (who:str, whom:str, how_much_should_pay:float)
    """


    df = pd.read_csv(filename)

    try:
        df["AmountInCUR"] = df.Currency.map(lambda x: exchange_rates[x]) * df.Amount
    except KeyError as k:
        raise ValueError("Exchange rate for {} not specified".format(k.args[0]))


    df_people = pd.DataFrame({"Name": people, "AmountInCUR": [0] * len(people), "For": ["All"] * len(people)})

    df = df.append(df_people)

    money_spent = {}
    for person in people:
        money_spent.setdefault(person, 0)
        for amount, forwhom in zip(df.AmountInCUR, df.For):
            fwl = forwhom.split()
            if fwl[0] == "All":
                money_spent[person] += amount / len(people)
            elif fwl[0] == "AllBut" and person not in fwl[1:]:
                money_spent[person] += amount / (len(people) - len(fwl[1:]))
            elif fwl[0] != "AllBut" and person in fwl:
                money_spent[person] += amount / len(fwl)
    print(money_spent)

    #just creating pd.Dataframe from dict
    tmp = pd.DataFrame(list(zip(*money_spent.items()))).transpose()
    tmp.columns = ["Name", "MoneySpent"]

    sums = df.filter(["Name", "AmountInCUR"]).groupby("Name").sum()

    sums = pd.merge(tmp, sums, left_on="Name", right_index=True)

    sums["ShouldPay"] = sums.MoneySpent - sums.AmountInCUR

    howto = sums.sort("ShouldPay")

    payments = []

    topay = list(map(list, zip(howto.ShouldPay.map(lambda x: round(x, decimal_places)), howto.Name)))

    least = 0
    most = len(topay)-1

    while len(topay) > 1:
        print(topay)
        pay, who = topay.pop()
        topay[0][0] += pay
        payments.append((who, topay[0][1], round(pay, decimal_places)))
        topay.sort()

    return payments


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Determines the least possible amount of transactions to settle debts")
    parser.add_argument("-c", "--currency", default="CZK", help="Currency in which the debts will be settled")
    parser.add_argument("-x", "--exchange-rates", default="", help="Exchange rates in the form 'USD:20,EUR:27.09'")
    parser.add_argument("-p", "--people", required=True, help="List of all the people involved, for example 'Adam,David'. Spaces in names not allowed.")
    parser.add_argument("-d", "--decimal_places", default=2, help="Number of decimal places to which amounts should be rounded.")
    parser.add_argument("file.csv")


    args = vars(parser.parse_args())

    exchange_rates = {args["currency"]: 1}
    for pair in args["exchange_rates"].split(","):
        if not pair:
            continue

        try:
            cur, rate_str = pair.split(":")
        except ValueError:
            raise ValueError("Bad format of exchange rate string:'{}' Should be for example 'CUR:12.3'".format(pair))

        rate = float(rate_str)

        exchange_rates[cur] = rate
            
    people = args["people"].split(",")

    print(settle(people, exchange_rates, args["file.csv"], decimal_places=args["decimal_places"]))
