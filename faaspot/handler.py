import os
import json
import urlparse
from decimal import Decimal

from box import Box
from slackclient import SlackClient
from forex_python.bitcoin import BtcConverter
from forex_python.converter import CurrencyRates
from forex_python.converter import CurrencyCodes

DEFAULT_BASE_CURRENCY_CODE = 'USD'


def get_currency(event, context):
    query_params = event.get("query", {})
    params = Box(query_params)
    print (params)
    base_currency_code = query_params.get('base_code')
    dest_currency_code = query_params.get('dest_code')
    amount = query_params.get('amount')
    date = query_params.get('date')
    from_currency_code = base_currency_code or DEFAULT_BASE_CURRENCY_CODE
    amount = Decimal('1')
    c = CurrencyRates(force_decimal=True)
    info = c.get_rates(from_currency_code)
    return _build_response(info)


def get_currency_name(currency_code):
    c = CurrencyCodes()
    return c.get_currency_name(currency_code)


def get_bitcoin_value(event, context):
    query_params = event.get("query", {})
    params = Box(query_params)
    print (params)
    currency_code = DEFAULT_BASE_CURRENCY_CODE
    b = BtcConverter(force_decimal=True)
    price = b.get_latest_price(currency_code)
    return _build_response({currency_code: price})


def _build_response(response, stringify=True):
    response = json.dumps(response) if stringify else response
    return {
        'statusCode': 200,
        'body': response,
        'headers': {"Content-Type": "application/json"}
    }