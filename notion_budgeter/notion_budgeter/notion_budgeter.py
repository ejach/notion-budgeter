from os import getenv
from datetime import datetime, timedelta
from json import dumps

import plaid
from plaid.api import plaid_api as papi
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from requests import post, exceptions
from sqlalchemy import insert

from notion_budgeter.models.Transactions import Transactions
from notion_budgeter.models.decorators.decorators import db_connector


def send_req(body):
    try:
        post(getenv('base_url'), headers={'Content-Type': 'application/json'}, data=dumps(body))
    except exceptions.ConnectionError as e:
        print('Base URL invalid, please try again' + '\n' + str(e))


def get_plaid_info():
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
    return response['transactions']


@db_connector
def send_to_notion(**kwargs):
    db = kwargs.pop('connection')
    transactions = get_plaid_info()
    get_ids = db.query(Transactions.t_id)
    ids = [i[0] for i in db.execute(get_ids).fetchall()]
    for x in transactions:
        if transactions and x['transaction_id'] not in ids:
            dic = {
                'amount': x['amount'],
                'date': datetime.strftime(x['date'], '%Y-%m-%dT%H:%M:%SZ'),
                'expense': x['name']
            }
            send_req(dic)
            insert_id = insert(Transactions).values(t_id=x['transaction_id'])
            db.execute(insert_id)
            db.commit()
