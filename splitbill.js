// Matěj Kocián 2017
// https://github.com/nimral/splitbill
//
// google sheets macro determining how to settle debts among n people with at
// most n-1 payments
//
// Usage: google sheet -> tools -> script editor -> insert code, save
// back to google sheet -> insert something like =splitbill(A2:E6) or 
// =splitbill(A2:E6; "USD") into a cell


function trim(s) { 
  return ( s || '' ).replace( /^\s+|\s+$/g, '' );
}


function inc(obj, k, v) {
  if (!obj.hasOwnProperty(k)) {
      obj[k] = 0;
    }
    obj[k] += v;
}


function append(obj, k, v) {
  if (!obj.hasOwnProperty(k)) {
    obj[k] = [];
  }
  obj[k].push(v)
}


/**
 * Returns the exchange rate of two currencies.
 *
 * @param {from} input The currency which would be bought.
 * @param {to} input The currency in which we would pay.
 * @return The exchange rate.
 * @customfunction
 */
function get_exchange_rate(from, to) {
  return JSON.parse(
    UrlFetchApp.fetch(
      'http://data.fixer.io/api/latest?access_key=b6e8822ec070884404992eb189c040c2&base=' + from + '&symbols=' + to
    ).getContentText()
  )["rates"][to];
}


/**
 * Creates list of at most n-1 payments to settle debts among n people.
 *
 * @param {bills} input The bills – rows with the name of the payer, item,
 * amount, currency and list of people, for whom the money has been spent.
 * @param {base_currency} Code of the currency, in which the transactions will be made. Default "CZK".
 * @param {lang} Language of the output ("cs" (default) or "en").
 * @param {explain} Should we output explanation? Default true.
 * @return Payments to be made – rows with payer, payee, amount and currency.
 * @customfunction
 */
function splitbill(bills, base_currency, lang, explain) {

  if (typeof(base_currency) === "undefined") {
    base_currency = "CZK";
  }
  output_base_currency = base_currency;  // string users will see

  if (typeof(lang) === "undefined") {
    lang = "cs";
  }
  if (lang != "cs" && lang != "en") {
    return "Unknown lang '" + lang + "'. Please choose 'cs' or 'en'.";
  }

  if (typeof(explain) === "undefined") {
    explain = true;
  }

  // some currencies can be refered to by several names
  cannonical_name = function (name) {
    names = {
      "Kč": "CZK"
    }
    if (names.hasOwnProperty(name)) {
      return names[name];
    }
    return name;
  }

  // dict who -> how much he should pay
  should_pay = {}
  // dict who -> textual explanation of the result
  why_should_pay = {}
  for (i = 0; i < bills.length; i++) {

    // skip empty lines
    empty = true;
    for (j = 0; j < bills[i].length; j++) {
      if (bills[i][j] != "") {
        empty = false;
        break;
      }
    }
    if (empty) {
      continue;
    }

    // if "Kč" is used instead of "CZK" at any time, use it in the output
    if (bills[i][3] == "Kč" && output_base_currency == "CZK") {
      output_base_currency = "Kč";
    }

    payer = bills[i][0];
    amount = bills[i][2];

    // convert currencies
    currency = cannonical_name(bills[i][3]);
    if (currency != base_currency) {
      amount *= get_exchange_rate(currency, base_currency);
    }

    // count how much everyone should pay
    inc(should_pay, payer, -amount);

    people = bills[i][4].split(",").map(trim);
    payer_explained = false;
    for (j = 0; j < people.length; j++) {
      inc(should_pay, people[j], amount / people.length);

      // add explanation
      if (people[j] == payer) {
        payer_explained = true;
        append(why_should_pay, people[j], "-" + amount + "*(" + (people.length-1) +  "/" + people.length + ")");
      } else {
        append(why_should_pay, people[j], "" + amount + (people.length > 1 ? "/" + people.length : ""));
      }
    }

    // add explanation in the case that the payer was not among the people he paid for
    if (!payer_explained) {
      append(why_should_pay, payer, "-" + amount);
    }

  }
  people = Object.keys(should_pay);

  topay = [] // array of pairs (should pay, name)
  for (i = 0; i < people.length; i++) {
    person = people[i];
    if (should_pay[person] != 0) {
      topay.push([should_pay[person], person]);
    }
  }
  topay.sort();

  // create list of payments to be made in order to settle all debts
  // list of tuples (who, to whom, how much should pay, currency)
  payments = [];
  while (topay.length > 1) {
    tmp = topay[topay.length - 1];
    topay.pop();
    who = tmp[1];
    amount = tmp[0];

    if (amount > 0) {
      topay[0][0] += amount;
      payments.push([who, topay[0][1], amount, output_base_currency]);
    }
    topay.sort();
  }

  if (lang == "cs") {
    header = [["Kdo", "Komu", "Kolik"]];
  } else {
    header = [["Who", "To whom", "How much"]];
  }

  explanation = [];
  if (explain) {
    if (lang == "cs") {
      explanation = [
        [],
        ["Každý by měl dostat součet částek, které mu dluží ostatní, minus součet částek, které dluží ostatním on."],
        ["Není ale důležité, jestli peníze dostane přímo od původních dlužníků."],
        ["Kolik kdo celkem dluží:"]
      ];
    }
    if (lang == "en") {
      explanation = [
        [],
        ["Everybody should get the sum of money others owe them minus the sum of money they owe others."],
        ["But it is not important to get the money directly from the original debtors."],
        ["How much should each person pay:"]
      ];
    }

    people = Object.keys(why_should_pay);
    for (i = 0; i < people.length; i++) {
      person = people[i];
      explanation.push([person, should_pay[person], "= " + why_should_pay[person].join(" + ").replace(/\+ -/g, "- ")]);
    }

  }

  return header.concat(payments).concat(explanation);
}
