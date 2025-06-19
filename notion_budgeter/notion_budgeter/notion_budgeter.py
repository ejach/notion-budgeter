from ast import literal_eval
from base64 import b64encode
from datetime import datetime, timedelta, timezone
from json import loads
from os import getenv, environ
from sys import exit
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlencode

from notion_client import Client
from sqlalchemy import insert

from notion_budgeter.logger.logger import Logger
from notion_budgeter.models.Transactions import Transactions
from notion_budgeter.models.decorators.decorators import db_connector


def get_sfin_info():
    base_url = 'https://beta-bridge.simplefin.org/simplefin/accounts'

    try:
        days_back = int(getenv('simplefin_days_back', '2'))
    except ValueError:
        days_back = 2

    # Construct the URL
    start_date = int((datetime.now(timezone.utc) - timedelta(days=days_back)).timestamp())
    query = {'start-date': start_date}
    include_pending = getenv('include_pending', 'false').lower() in ['1', 'true', 'yes']
    if include_pending:
        query['pending'] = 1
    url = f'{base_url}?{urlencode(query)}'

    # Construct the Auth/Header
    username, password = getenv('simplefin_username'), getenv('simplefin_password')
    credentials = f'{username}:{password}'.encode()
    auth_header = b64encode(credentials).decode()
    headers = {
        'Authorization': f'Basic {auth_header}',
        'User-Agent': 'notion-budgeter/1.0 (https://github.com/ejach/notion-budgeter)',
    }

    req = Request(url, headers=headers)
    try:
        with urlopen(req) as response:
            data = loads(response.read().decode())
    except HTTPError as e:
            exit(f'HTTP Error {e.code}: {e.reason}')
    except URLError as e:
        exit(f'Failed to reach the server: {e.reason}')

    return [
        {
            **tx,
            'transacted_at': datetime.fromtimestamp(tx['transacted_at'], tz=timezone.utc).strftime('%Y-%m-%d'),
            'amount': -float(tx['amount'])
        } for tx in data['accounts'][0]['transactions']
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

    # Initialize Notion
    notion_secret = getenv('notion_secret')
    notion_db_query = getenv('notion_db')
    if not notion_secret and not notion_db_query:
        exit('Notion environment variables not found. Please check your environment.')
    notion = Client(auth=notion_secret)

    notion_custom_property = None
    try:
        if 'notion_custom_property' in environ:
            notion_custom_property = literal_eval((getenv('notion_custom_property')))
    except SyntaxError as e:
        exit(f'Syntax error. Please check the formatting of your notion_custom_property \n{e}')

    for x in transactions:
        date = x['transacted_at']
        t_id = x['id']
        if transactions and t_id not in ids and x['description'] not in excluded:
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
                exit(f'Notion error: {notion_page["message"]}')
            Logger.log.info(f'{date} - Logging transaction {t_id}')
            insert_into_db(insert(Transactions).values(t_id=t_id))
