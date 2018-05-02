import os
import json
import urlparse
import pycountry

from box import Box
from forex_python.bitcoin import BtcConverter
from forex_python.converter import CurrencyRates
from forex_python.converter import CurrencyCodes

from moneyed import Money
from moneyed.localization import format_money


DEFAULT_BASE_CURRENCY_CODE = 'USD'


def format_value(value, thousands_separator=None, ndigits=None):
    if thousands_separator and ndigits:
        return "{:,.{}f}".format(value, ndigits)
    elif ndigits:
        return  "{:.{}f}".format(value, ndigits)
    elif thousands_separator:
        return  "{:,}".format(value)
    return value


def get_currency(args):
    source_currency_code = args.get('source_currency')
    target_currency_code = args.get('target_currency')
    ndigits = args.get('ndigits')
    thousands_separator = args.get('thousands_separator')    
    source_currency_code = source_currency_code.upper()
    print("source_currency_code: {}".format(source_currency_code))
    print("target_currency_code: {}".format(target_currency_code))
    response = {'source': source_currency_code}
    c = CurrencyRates(force_decimal=False)
    info = c.get_rates(source_currency_code)    
    info =  {k: format_value(v, thousands_separator, ndigits) for k, v in info.iteritems()}
    if target_currency_code:
        target_currency_code = target_currency_code.upper()
        if target_currency_code not in info:
            raise Exception("Unrecognized `{}` currency".format(target_currency_code))
        response['target'] = target_currency_code
        info = info.get(target_currency_code)
    response['currency'] = info
    return response


def currency_exchange(args):
    source_currency_code = args.get('source_currency')
    target_currency_code = args.get('target_currency')
    amount = args.get('amount')
    ndigits = args.get('ndigits')
    thousands_separator = args.get('thousands_separator')
    if not amount:
        # for some reason, args.get('amount', '1') doesn't work..
        amount = 1
    source_currency_code = source_currency_code.upper()
    target_currency_code = target_currency_code.upper()
    print("source_currency_code: {}".format(source_currency_code))
    print("target_currency_code: {}".format(target_currency_code))
    print("amount: {}".format(amount))
    print("thousands_separator: {}".format(thousands_separator))
    amount = float(amount)
    c = CurrencyRates(force_decimal=False)
    value = c.convert(source_currency_code, target_currency_code, amount)   
    value = format_value(value, thousands_separator, ndigits)
    return {'source': source_currency_code, 'target': target_currency_code, 'amount': amount, 'value': value}


def get_country_currency(args):
    country_lookup = args.get('country')
    # lookup (vs get) will perform case insensitively without knowing which key the value may match 
    # it's instead of: country = pycountry.countries.get(name=name)
    try:
        print "Searching for: {}".format(country_lookup)
        country = pycountry.countries.lookup(country_lookup)
    except Exception:
        return {'error': 'failed to find `{}`'.format(country)}
    try:
        currency = pycountry.currencies.get(numeric=country.numeric)
    except Exception:
        return {'error': 'failed to find currency of `{}`'.format(country.name)}
    return {'country_name': country.name, 'country_code': country.alpha_2, 'currency_code': currency.alpha_3, 'currency_name': currency.name}


def get_formatted_money(args):
    currency = args.get('currency')
    amount = args.get('amount')
    print ("currency: {}".format(currency))
    print ("amount: {}".format(amount))
    price = Money(amount=amount, currency=currency)
    # format_money(price, locale='en_US')
    return {'value': format_money(price)}


def get_bitcoin_value(event, context):
    query_params = event.get("query", {})
    params = Box(query_params)
    print (params)
    currency_code = DEFAULT_BASE_CURRENCY_CODE
    b = BtcConverter(force_decimal=True)
    price = b.get_latest_price(currency_code)
    return {currency_code: price}

# print get_currency({'source_currency': 'USD', 'target_currency': 'ILS'})
# print convert_currency({'source_currency': 'USD', 'target_currency': 'ILS', 'amount': '1'})
print get_country_currency({'country': 'France'})