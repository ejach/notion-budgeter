from ast import literal_eval
from datetime import datetime, timedelta
from os import getenv, environ, path
from sys import exit

from notion_client import Client
from requests import get
from sqlalchemy import insert

from notion_budgeter.logger.logger import Logger
from notion_budgeter.models.Transactions import Transactions
from notion_budgeter.models.decorators.decorators import db_connector


def get_teller_info():
    url = 'https://api.teller.io/accounts/%s/transactions' % getenv('teller_account_id')

    # Access token and paths to the certificate and key files
    cert_path = getenv('teller_cert_path')
    key_path = getenv('teller_key_path')
    access_token = getenv('teller_access_token')
    start_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    end_date = datetime.today().replace(hour=23, minute=59, second=59, microsecond=0)

    for p in (cert_path, key_path):
        if not path.exists(p):
            exit('One or more Teller .pem path is incorrect.')

    # Making the request with the certificate and key
    response = get(url, cert=(cert_path, key_path), auth=(access_token, ''))
    results = response.json()

    if response.status_code == 403:
        exit('Teller request failed: %s' % results['error']['message'])
    return [i for i in results if start_date <= datetime.strptime(i['date'], '%Y-%m-%d') <= end_date and i['status'] == 'pending']


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
    transactions = get_teller_info()
    ids = [i[0] for i in get_from_db(Transactions.t_id).fetchall()]
    excluded = environ.get('excluded', '').split(',') or [environ.get('excluded')]
    for x in transactions:
        date = x['date']
        if transactions and x['id'] not in ids and x['description'] not in excluded:
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
                    'Expense': {'title': [{'text': {'content': x['description']}}]},
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
                '%s - Logging transaction %s***' % (date, x['id']))
            insert_into_db(insert(Transactions).values(t_id=x['id']))
