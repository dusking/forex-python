import os
import json
import urlparse
import requests
import ipaddress
import threading

import jsonschema
from functools import wraps
from jsonschema import validate
from jsonschema import Draft4Validator
from jsonschema.exceptions import ValidationError, SchemaError

import base64
import hashlib

from Crypto import Random
from Crypto.Cipher import AES

from handler import get_currency, currency_exchange, get_country_currency


def unpad(data):
    return data[0:-ord(data[-1])]


def decrypt(hex_data):
    key = 'WmFKzhC3YRmEU4dPY3hza8HUu7653Gg3'
    iv = 'ZS9ATh5Wz4jUN895'
    data = ''.join(map(chr, bytearray.fromhex(hex_data)))
    aes = AES.new(key, AES.MODE_CBC, iv)
    data = unpad(aes.decrypt(data))
    return base64.b64decode(data)


def validate_token(token):
    user_data = ''
    if not token:
        return {'error': "missing user token"}
    try:
        user_data = decrypt(token.replace('Basic ', ''))
        print ("user_data: {0}".format(user_data))
    except ValueError:
        return {'error': '`{}` does not appear to be a valid token'.format(token)}
    return {'user_data': user_data}


def callPost(body):    
    print ('going to send `google-bigquery` request.. body: {}'.format(body))
    headers = {"Content-Type":"application/json", "Token":"Basic 62646018047677d2f204ffae7dac388bc4cb227d963b729d"}    
    send_message_url = 'https://us-central1-faaspotit.cloudfunctions.net/google-bigquery'
    requests.post(send_message_url, data=json.dumps(body), headers=headers)


def update_usage(user_id, user_ip_addr, function_id, function_name):
    body = {"user_id": user_id, 'source_ip': user_ip_addr, 'function_id': function_id, 'function_name': function_name}
    th = threading.Thread(target=callPost, args=[body])
    th.daemon = True
    th.start()


def endpoint(schema=None):
    def endpoint_wrapper(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            event, context = args
            print ("event: {0}".format(event))
            print ("context: {0}".format(context))
            body = event.get("body", "{}")
            
            try:
                body = json.loads(body)
            except ValueError:
                body = urlparse.parse_qs(body)  
                body = {k: v[0] for k, v in body.iteritems()}

            if schema:
                try:
                    validate(body, schema)
                except (ValidationError, SchemaError) as ex:
                    element = ex.path[0]
                    message = ex.message
                    err_message = '{} - {}'.format(element, message)
                    return {
                        'statusCode': 400,
                        'body': json.dumps({'error': err_message}),
                        'headers': {"Content-Type": "application/json"}
                    }
                
            headers = event.get("headers", {})        
            token = headers.get('Token')    
            user_ip = headers.get('X-Forwarded-For')

            result = validate_token(token)
            err = result.get('error')
            if err:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': err}),
                    'headers': {"Content-Type": "application/json"}
                }
            user_data = result.get('user_data')
            user_id = user_data.split(':')[0]
            function_name = event.get('uri').split('/')[-1]
            function_id = context.get('functionId')
            update_usage(user_id, user_ip, function_id, function_name)
            
            try:
                response = json.dumps(func(body))    
            except Exception as ex:
                return {
                        'statusCode': 400,
                        'body': json.dumps({'error': str(ex)}),
                        'headers': {"Content-Type": "application/json"}
                    }
            return {
                'statusCode': 200,
                'body': response,
                'headers': {"Content-Type": "application/json"}
            }
        return wrapper
    return endpoint_wrapper


get_currency_schema = {
    'required': ['source_currency'],
    'properties':  {
        'ndigits': {'type': 'integer'},
        'source_currency': {'type': 'string'},
        'target_currency': {'type': 'string'}
    }}

@endpoint(get_currency_schema)
def wrapper_get_currency(*args, **kwargs):
    return get_currency(*args, **kwargs)

wrapper_exchange_schema = {
    'required': ['source_currency'],
    'properties':  {
        'ndigits': {'type': 'integer'},
        'source_currency': {'type': 'string'},
        'target_currency': {'type': 'string'},
        'amount': {'type': 'number'},
        'ndigits': {'type': 'integer'},
        'thousands_separator': {'type': 'boolean'},
    }}

@endpoint(wrapper_exchange_schema)
def wrapper_exchange(*args, **kwargs):
    return currency_exchange(*args, **kwargs)


@endpoint()
def wrapper_country_currency(*args, **kwargs):
    return get_country_currency(*args, **kwargs)


# def wrapper_old(event, context):
#     print ("event: {0}".format(event))
#     print ("context: {0}".format(context))
#     body = event.get("body", "{}")
#     try:
#         body = json.loads(body)
#     except ValueError:
#         body = urlparse.parse_qs(body)  
#         body = {k: v[0] for k, v in body.iteritems()}
#     headers = event.get("headers", {})        
#     token = headers.get('Token')    
#     user_ip = headers.get('X-Forwarded-For')

#     result = validate_token(token)
#     err = result.get('error')
#     if err:
#         return {
#             'statusCode': 400,
#             'body': json.dumps({'error': err}),
#             'headers': {"Content-Type": "application/json"}
#         }
#     user_data = result.get('user_data')
#     user_id = user_data.split(':')[0]
#     function_name = event.get('uri').split('/')[-1]
#     function_id = context.get('functionId')
#     update_usage(user_id, user_ip, function_id, function_name)
    
#     response = json.dumps(get_currency(body))    
#     return {
#         'statusCode': 200,
#         'body': response,
#         'headers': {"Content-Type": "application/json"}
#     }


def wrapper_exchange_old(event, context):
    print ("event: {0}".format(event))
    print ("context: {0}".format(context))
    body = event.get("body", "{}")
    try:
        body = json.loads(body)
    except ValueError:
        body = urlparse.parse_qs(body)  
        body = {k: v[0] for k, v in body.iteritems()}
    headers = event.get("headers", {})        
    token = headers.get('Token')    
    user_ip = headers.get('X-Forwarded-For')

    result = validate_token(token)
    err = result.get('error')
    if err:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': err}),
            'headers': {"Content-Type": "application/json"}
        }
    user_data = result.get('user_data')
    user_id = user_data.split(':')[0]
    function_name = event.get('uri').split('/')[-1]
    function_id = context.get('functionId')
    update_usage(user_id, user_ip, function_id, function_name)
    
    response = json.dumps(currency_exchange(body))    
    return {
        'statusCode': 200,
        'body': response,
        'headers': {"Content-Type": "application/json"}
    }


def wrapper_country_currency_old(event, context):
    print ("event: {0}".format(event))
    print ("context: {0}".format(context))
    body = event.get("body", "{}")
    try:
        body = json.loads(body)
    except ValueError:
        body = urlparse.parse_qs(body)  
        body = {k: v[0] for k, v in body.iteritems()}
    headers = event.get("headers", {})        
    token = headers.get('Token')    
    user_ip = headers.get('X-Forwarded-For')

    result = validate_token(token)
    err = result.get('error')
    if err:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': err}),
            'headers': {"Content-Type": "application/json"}
        }
    user_data = result.get('user_data')
    user_id = user_data.split(':')[0]
    function_name = event.get('uri').split('/')[-1]
    function_id = context.get('functionId')
    update_usage(user_id, user_ip, function_id, function_name)
    
    response = json.dumps(get_country_currency(body))    
    return {
        'statusCode': 200,
        'body': response,
        'headers': {"Content-Type": "application/json"}
    }


# event = {u'body': u'{"source_currency":"usd","target_currency":"ils","ndigits":"2"}', u'uri': u'https://app-2bc38fc4-add-demo-execute-function1.spotinst.io/get_currency', u'headers': {u'Content-Length': u'63', u'Request-Source': u'external', u'X-Forwarded-Port': u'443', u'X-Forwarded-For': u'52.6.120.182', u'Host': u'app-2bc38fc4-add-demo-execute-function1.spotinst.io', u'Accept': u'application/json', u'User-Agent': u'curl/7.35.0', u'X-Real-IP': u'52.6.120.182', u'Token': u'Basic 1664d39eaa6eac4ac31cde6e5dd7f217bb528cfc9edb673883f061394076d934', u'X-Forwarded-Proto': u'https', u'X-Custom-ReferrerB': u'52.6.120.182', u'X-Custom-ReferrerA': u'52.6.120.182', u'Content-Type': u'application/json'}, u'query': {}}
# context = {u'environmentId': u'env-b6436fc5', u'functionVersion': 10, u'timeoutInMillis': 30000, u'functionName': u'fx-45886253', u'memoryLimitInMB': 128, u'functionId': u'fx-45886253', u'invocationId': u'invoc-f6aa0e4d9818'}
# print wrapper_get_currency(event, context)