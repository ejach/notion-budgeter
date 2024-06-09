from ast import literal_eval
from datetime import datetime, timedelta
from os import getenv, environ, path
from sys import exit

import plaid
from notion_client import Client
from plaid.api import plaid_api as papi
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from requests import get
from sqlalchemy import insert, desc, cast, select, Integer

from notion_budgeter.logger.logger import Logger
from notion_budgeter.models.Transactions import Transactions
from notion_budgeter.models.decorators.decorators import db_connector


def get_plaid_info():
    configuration = plaid.Configuration(
        host=plaid.Environment.Sandbox if 'plaid_environment' in environ and
                                          getenv('plaid_environment').lower() == 'sandbox'
        else plaid.Environment.Development,
        api_key={
            'clientId': getenv('plaid_client_id'),
            'secret': getenv('plaid_secret'),
        }
    )

    yesterday = datetime.today() - timedelta(days=1)
    today = datetime.today()
    request = papi.TransactionsGetRequest(
        access_token=getenv('plaid_access_token'),
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
def get_teller_info(**kwargs):
    url = 'https://api.teller.io/accounts/%s/transactions' % getenv('teller_account_id')

    # Access token and paths to the certificate and key files
    cert_path = getenv('teller_cert_path')
    key_path = getenv('teller_key_path')
    access_token = getenv('teller_access_token')

    for p in (cert_path, key_path):
        if not path.exists(p):
            exit('One or more Teller .pem path is incorrect.')

    db = kwargs.pop('connection')
    stmt = select(Transactions.t_id).order_by(desc(cast(Transactions.id, Integer)))
    last_id = db.execute(stmt).first()

    # Making the request with the certificate and key
    response = get(url, cert=(cert_path, key_path), auth=(access_token, ''), params={'from_id': last_id})
    results = response.json()

    if response.status_code == 403:
        exit('Telly request failed: %s' % results['error']['message'])

    return results


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
    teller_enabled = bool(getenv('teller_enabled'))
    transaction_info = get_teller_info() if teller_enabled else get_plaid_info()
    transactions = transaction_info if teller_enabled else transaction_info['transactions']
    ids = [i[0] for i in get_from_db(Transactions.t_id).fetchall()]
    excluded = environ.get('excluded', '').split(',') or [environ.get('excluded')]
    valid_entry = lambda tid, name: tid not in ids and name not in excluded
    for x in transactions:
        date = x['date'] if teller_enabled else datetime.strftime(x['date'], '%Y-%m-%dT%H:%M:%SZ')
        if transactions and valid_entry(x['id'], x['description']) if teller_enabled else valid_entry(
                x['transaction_id'], x['name']):
            if 'notion_secret' in environ and 'notion_db' in environ:
                notion = Client(auth=getenv('notion_secret'))
                db_query = notion.search(**{
                    'query': getenv('notion_db'),
                    'property': 'object',
                    'value': 'database'
                })

                if len(db_query['results']) == 0:
                    exit('Notion database not found, please check your configuration.')

                db_id = db_query['results'][0]['id']
                db_obj = notion.databases.retrieve(database_id=db_id)
                props = {
                    'Expense': {'title': [{'text': {'content': x['description'] if teller_enabled else x['name']}}]},
                    'Amount': {'number': float(x['amount'])},
                    'Date': {'date': {'start': date}},
                }

                try:
                    if 'notion_custom_property' in environ:
                        props.update(literal_eval((getenv('notion_custom_property'))))
                except SyntaxError as e:
                    exit('Syntax error. Please check the formatting of your notion_custom_property \n%s' % e)

                notion_page = notion.pages.create(
                    parent={'database_id': db_obj['id']},
                    properties=props,
                    icon={'emoji': environ.get('notion_icon', '\U0001F9FE'.encode('raw-unicode-escape')
                                               .decode('unicode-escape'))}
                )
                if notion_page['object'] == 'error':
                    exit('Notion error: %s' % notion_page['message'])
            else:
                exit('Notion environment variables not found. Please check your environment.')
            Logger.log.info(
                '%s - Logging transaction %s***' % (date, x['id'] if teller_enabled else x['transaction_id'][:-30]))
            insert_into_db(insert(Transactions).values(t_id=x['id'] if teller_enabled else ['transaction_id']))
