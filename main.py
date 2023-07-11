from os import getenv
from datetime import datetime, timedelta
from json import dumps

import plaid
from plaid.api import plaid_api as papi
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from requests import post, exceptions
from sqlalchemy import text

from models.Transactions import engine


def send_req(body):
    try:
        post(getenv('base_url'), headers={'Content-Type': 'application/json'}, data=dumps(body))
    except exceptions.ConnectionError as e:
        print('Base URL invalid, please try again' + '\n' + str(e))


def db_conn(query):
    db = engine.begin()
    with db as conn:
        return conn.execute(query)


configuration = plaid.Configuration(
    host=plaid.Environment.Development,
    api_key={
        'clientId': getenv('client_id'),
        'secret': getenv('secret'),
    }
)

rn = datetime.today()
rn_minus = datetime.today() - timedelta(hours=1)
request = papi.TransactionsGetRequest(
    access_token=getenv('access_token'),
    start_date=datetime.date(rn),
    end_date=datetime.date(rn_minus),
    options=TransactionsGetRequestOptions(
        include_personal_finance_category=True
    )
)
api_client = plaid.ApiClient(configuration)
client = papi.PlaidApi(api_client)
response = client.transactions_get(request)
transactions = response['transactions']
arr, dic = [], {}

ids = [i[1] for i in db_conn(text('SELECT * FROM transactions;')).fetchall()]
for x in transactions:
    if x['transaction_id'] not in ids:
        dic = {
            'amount': x['amount'],
            'date': datetime.strftime(x['date'], '%Y-%m-%dT%H:%M:%SZ'),
            'expense': x['name']
        }
        send_req(dic)
        db_conn(text('INSERT INTO transactions (t_id) VALUES ("%s");' % x['transaction_id']))
