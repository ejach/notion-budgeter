### notion-budgeter
[![PyPI](https://img.shields.io/pypi/v/plaid-python?logo=python&label=plaid-python&style=flat-square&color=FFD43B)](https://pypi.org/project/plaid-python/)
[![PyPI](https://img.shields.io/pypi/v/notion-client?logo=python&label=notion-client&style=flat-square&color=FFD43B)](https://pypi.org/project/notion-client/)
[![PyPI](https://img.shields.io/pypi/v/schedule?logo=python&label=schedule&style=flat-square&color=FFD43B)](https://pypi.org/project/schedule/)
[![PyPI](https://img.shields.io/pypi/v/SQLAlchemy?logo=python&label=SQLAlchemy&style=flat-square&color=FFD43B)](https://pypi.org/project/SQLAlchemy/)

Keeps a given Notion database up to date with transactions using Plaid.

#### docker-compose.yml
```yml
version: '3.7'
services:
  notion_budgeter:
    image: ghcr.io/ejach/notion-budgeter
    container_name: notion_budgeter
    environment:
      - access_token=<access_token>
      - client_id=<client_id>
      - secret=<secret>
      - environment=<development OR sandbox> # optional, defaults to development
      - data_dir=<data_dir>
      - notion_secret=<notion_secret>
      - notion_db=<notion_db>
      - custom_property=<custom_property> # optional
    volumes:
      - /path/to/data:/path/to/data
    restart: unless-stopped
```
| Variable         | Description                                                                   | Required |
|------------------|-------------------------------------------------------------------------------|----------|
| `access_token`   | Token associated with financial account (see below)                           | ✅        |
| `client_id`      | ID associated with a Plaid account                                            | ✅        |
| `secret`         | Key associated with environment                                               | ✅        |
| `data_dir`       | Path to where the database file should be stored                              | ✅        |
| `environment`    | What Plaid environment should the program run in (`development` or `sandbox`) | ❌        |
| `notion_secret` | The secret token associated with your Notion integration                             | ✅        |
| `notion_db` | The database name that you want the data to be stored in (case-sensitive)                            | ✅        |
| `custom_property` | Custom property in the format that Notion expects (see below)                            | ❌        |





#### Installation

Pre-requisites:
- [Notion](https://notion.so) account
- A Notion Integration added to a desired database (see the [Notion guide](https://www.notion.so/help/create-integrations-with-the-notion-api))
- [Plaid](https://dashboard.plaid.com/signup) account with a [Development API `Secret`](https://plaid.com/docs/quickstart/glossary/#development) an account `client_id`, and an `access_token` from a connected financial account (see the [Quickstart](https://github.com/plaid/quickstart) repository)

> NOTE: If you get a "[Connectivity not supported](https://plaid.com/docs/link/troubleshooting/#missing-institutions-or-connectivity-not-supported-error)" error when using the Quickstart repository to get an `access_token`, follow [this](https://github.com/plaid/plaid-postman#making-api-calls-with-real-data-in-production-or-development) guide.

____
#### Properties this program expects

```bash
'Expense' -> type: text
'Amount' -> type: number
'Date' -> type: date
```
You must format your Notion database to have these properties.



#### How to format Custom Properties

The program expects a Python-like dictionary:


```python
{'Category': {'type': 'multi_select', 'multi_select': [{'name': '\u2754Uncategorized'}]}}
```


Or a list of Python-like dictionaries:


```python
{'Category': {'type': 'multi_select', 'multi_select': [{'name': '\u2754Uncategorized'}]}, 
'Comment': {'type': 'rich_text', 'rich_text': [{'type': 'text', 'text': { 'content': 'Hello World' }}]}}
```


When adding these to your environment, they need to be encapsulated in quotes `""`


More information on this format can be found [Here](https://developers.notion.com/reference/database#database-property).