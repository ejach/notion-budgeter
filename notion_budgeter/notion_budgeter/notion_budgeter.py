from ast import literal_eval
from datetime import datetime, timedelta
from os import getenv, environ, path
from sys import exit

from notion_client import Client
from requests import get
from requests.auth import HTTPBasicAuth
from sqlalchemy import insert

from notion_budgeter.logger.logger import Logger
from notion_budgeter.models.Transactions import Transactions
from notion_budgeter.models.decorators.decorators import db_connector


def get_sfin_info():
    url = 'https://beta-bridge.simplefin.org/simplefin/accounts'

    # Include pending expenses
    include_pending = getenv('include_pending', 'false').lower() in ['1', 'true', 'yes']
    if include_pending:
        url = f'{url}?pending=1'


    username, password = getenv('simplefin_username'), getenv('simplefin_password')
    start_date = int((datetime.utcnow() - timedelta(days=2)).timestamp())


    # Making the request with the start-date parameter
    response = get(
        url,
        auth=HTTPBasicAuth(username, password),
        params={'start-date': start_date}
    )
    results = response.json()

    if not response.ok:
        exit('SimpleFin request failed: %s' % results['errors'])

    return [
        {
            **tx,
            'transacted_at': datetime.utcfromtimestamp(tx['transacted_at']).strftime('%Y-%m-%d'),
            'amount': -float(tx['amount'])
        } for tx in results['accounts'][0]['transactions']
    ]


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
    transactions = get_sfin_info()
    ids = [i[0] for i in get_from_db(Transactions.t_id).fetchall()]
    excluded = environ.get('excluded', '').split(',') or [environ.get('excluded')]

    notion_secret = getenv('notion_secret')
    notion_db_query = getenv('notion_db')
    if not notion_secret and not notion_db_query:
        exit('Notion environment variables not found. Please check your environment.')
    # Initialize Notion
    notion = Client(auth=notion_secret)

    notion_custom_property = None
    try:
        if 'notion_custom_property' in environ:
            notion_custom_property = literal_eval((getenv('notion_custom_property')))
    except SyntaxError as e:
        exit('Syntax error. Please check the formatting of your notion_custom_property \n%s' % e)

    for x in transactions:
        date = x['transacted_at']
        if transactions and x['id'] not in ids and x['description'] not in excluded:
            db_query = notion.search(**{
                'query': notion_db_query,
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

            if notion_custom_property:
                props.update(notion_custom_property)

            notion_page = notion.pages.create(
                parent={'database_id': db_obj['id']},
                properties=props,
                icon={'emoji': environ.get('notion_icon', '\U0001F9FE'.encode('raw-unicode-escape')
                                           .decode('unicode-escape'))}
            )
            if notion_page['object'] == 'error':
                exit('Notion error: %s' % notion_page['message'])
            Logger.log.info(
                '%s - Logging transaction %s***' % (date, x['id']))
            insert_into_db(insert(Transactions).values(t_id=x['id']))
