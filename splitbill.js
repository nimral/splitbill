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
      'http://api.fixer.io/latest?base=' + from + '&symbols=' + to
    ).getContentText()
  )["rates"][to];
}


/**
 * Creates list of at most n-1 payments to settle debts among n people.
 *
 * @param {bills} input The bills – rows with the name of the payer, item,
 * amount, currency and list of people, for whom the money has been spent.
 * @return Payments to be made – rows with payer, payee, amount and currency.
 * @customfunction
 */
function splitbill(bills, base_currency) {

  if (typeof(base_currency) === "undefined") {
    base_currency = "CZK";
  }
  output_base_currency = base_currency;  // string users will see
  
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
    
    // convert currencies
    currency = cannonical_name(bills[i][3]);
    if (currency != base_currency) {
      bills[i][2] *= get_exchange_rate(currency, base_currency);
    }
    
    // count how much everyone should pay
    inc(should_pay, bills[i][0], -bills[i][2]);
    
    people = bills[i][4].split(",").map(trim);
    for (j = 0; j < people.length; j++) {
      inc(should_pay, people[j], bills[i][2] / people.length);
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
  
  return payments;
}
