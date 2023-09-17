from os import getenv, environ
from datetime import datetime, timedelta
from json import dumps

import plaid
from plaid.api import plaid_api as papi
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from requests import post, exceptions
from sqlalchemy import insert

from notion_budgeter.models.Transactions import Transactions
from notion_budgeter.models.decorators.decorators import db_connector
from notion_budgeter.logger.logger import Logger


def send_req(body):
    try:
        post(getenv('base_url'), headers={'Content-Type': 'application/json'}, data=dumps(body))
    except exceptions.ConnectionError as e:
        Logger.log.exception('Base URL invalid, please try again' + '\n' + str(e))


def get_plaid_info():
    configuration = plaid.Configuration(
        host=plaid.Environment.Sandbox if 'environment' in environ and getenv('environment').lower() == 'sandbox'
        else plaid.Environment.Development,
        api_key={
            'clientId': getenv('client_id'),
            'secret': getenv('secret'),
        }
    )

    yesterday = datetime.today() - timedelta(days=1)
    today = datetime.today()
    request = papi.TransactionsGetRequest(
        access_token=getenv('access_token'),
        start_date=datetime.date(yesterday),
        end_date=datetime.date(today),
        options=TransactionsGetRequestOptions(
            include_personal_finance_category=True
        )
    )
    api_client = plaid.ApiClient(configuration)
    client = papi.PlaidApi(api_client)
    response = client.transactions_get(request)
    return response


@db_connector
def get_from_db(item, **kwargs):
    db = kwargs.pop('connection')
    q = db.query(item)
    return db.execute(q)


@db_connector
def insert_into_db(q, **kwargs):
    db = kwargs.pop('connection')
    db.execute(q)
    db.commit()


def send_to_notion():
    plaid_info = get_plaid_info()
    transactions = plaid_info['transactions']
    ids = [i[0] for i in get_from_db(Transactions.t_id).fetchall()]
    acc_ids = dict(enumerate(set([i['account_id'] for i in plaid_info['accounts']]), start=1))
    for x in transactions:
        if transactions and x['transaction_id'] not in ids:
            date = datetime.strftime(x['date'], '%Y-%m-%dT%H:%M:%SZ')
            Logger.log.info('%s - Logging transaction %s***' % (date, x['transaction_id'][:-30]))
            a_id = [name for name, avail in acc_ids.items() if avail == x['account_id']]
            dic = {
                'amount': x['amount'],
                'date': date,
                'expense': x['name'],
                'acc_id': 'Account %s' % a_id[0]
            } if 'label_accounts' in environ and bool(getenv('label_accounts')) else {
                'amount': x['amount'],
                'date': date,
                'expense': x['name']
            }
            send_req(dic)
            insert_into_db(insert(Transactions).values(t_id=x['transaction_id']))
