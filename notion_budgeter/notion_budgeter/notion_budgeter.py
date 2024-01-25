from ast import literal_eval
from os import environ
from datetime import datetime, timedelta
from sys import exit

from notion_client import APIResponseError, Client
import plaid
from plaid.api import plaid_api as papi
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from sqlalchemy import insert

from notion_budgeter.models.Transactions import Transactions
from notion_budgeter.models.decorators.decorators import db_connector
from notion_budgeter.logger.logger import Logger


def get_plaid_info():
    configuration = plaid.Configuration(
        host=plaid.Environment.Sandbox if 'environment' in environ and environ.get('environment').lower() == 'sandbox'
        else plaid.Environment.Development,
        api_key={
            'clientId': environ.get('client_id'),
            'secret': environ.get('secret'),
        }
    )

    yesterday = datetime.today() - timedelta(days=1)
    today = datetime.today()
    request = papi.TransactionsGetRequest(
        access_token=environ.get('access_token'),
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
    excluded = environ.get('excluded', '').split(',') or [environ.get('excluded')]
    if 'notion_secret' in environ and 'notion_db' in environ:
        for x in transactions:
            if transactions and x['transaction_id'] not in ids and x['name'] not in excluded:
                date = datetime.strftime(x['date'], '%Y-%m-%dT%H:%M:%SZ')
                notion = Client(auth=environ.get('notion_secret'))
                db_query = notion.search(**{
                    'query': environ.get('notion_db'),
                    'property': 'object',
                    'value': 'database'
                })

                if len(db_query['results']) == 0:
                    exit('Notion database not found. Please check your configuration.')
                
                db_id = db_query['results'][0]['id']
                db_obj = notion.databases.retrieve(database_id=db_id)
                props = {
                    'Expense': {'title': [{'text': {'content': x['name']}}]},
                    'Amount': {'number': x['amount']},
                    'Date': {'date': {'start': date}},
                }

                if 'custom_property' in environ:
                    try:
                        props.update(literal_eval((environ.get('custom_property'))))
                    except SyntaxError as e:
                        exit('Syntax error. Please check the formatting of your custom_property: %s' % e)

                try:
                    notion.pages.create(
                        parent={'database_id': db_obj['id']},
                        properties=props
                    )
                except APIResponseError as e:
                    exit('Bad Request. Make sure your configuration is correct: %s' % e)

                Logger.log.info('%s - Logging transaction %s***' % (date, x['transaction_id'][:-30]))
                insert_into_db(insert(Transactions).values(t_id=x['transaction_id']))
    else:
        exit('Notion environment variables not found. Please check your environment.')
