### notion-budgeter
[![PyPI](https://img.shields.io/pypi/v/notion-client?logo=python&label=notion-client&style=flat-square&color=FFD43B)](https://pypi.org/project/notion-client/)
[![PyPI](https://img.shields.io/pypi/v/schedule?logo=python&label=schedule&style=flat-square&color=FFD43B)](https://pypi.org/project/schedule/)
[![PyPI](https://img.shields.io/pypi/v/SQLAlchemy?logo=python&label=SQLAlchemy&style=flat-square&color=FFD43B)](https://pypi.org/project/SQLAlchemy/)
[![PyPI](https://img.shields.io/pypi/v/Requests?logo=python&label=Requests&style=flat-square&color=FFD43B)](https://pypi.org/project/Requests/)

Keeps a given Notion database up to date with transactions using Teller.

#### docker-compose.yml
```yml
version: '3.7'
services:
  notion_budgeter:
    image: ghcr.io/ejach/notion-budgeter
    container_name: notion_budgeter
    environment:
      - data_dir=<data_dir>
      - notion_secret=<notion_secret>
      - notion_db=<notion_db>
      - notion_custom_property=<custom_property> # optional
      - notion_icon=<notion_icon> # optional, default 🧾
      - teller_account_id=<teller_account_id>
      - teller_access_token=<teller_access_token>
      - teller_cert_path=<teller_cert_path>
      - teller_key_path=<teller_key_path>
      - excluded=<expense_name> # optional
    volumes:
      - /path/to/data:/path/to/data
    restart: unless-stopped
```
| Variable                 | Description                                                                            | Required |
|--------------------------|----------------------------------------------------------------------------------------|--------|
| `data_dir`               | Path to where the database file should be stored                                       | ✅     |
| `notion_secret`          | The secret token associated with your Notion integration                               | ✅     |
| `notion_db`              | The database name that you want the data to be stored in (case-sensitive)              | ✅     |
| `teller_account_id`      | ID associated with your Teller account                                                 | ✅      |
| `teller_access_token`    | Token associated with your Teller account                                              | ✅      |
| `teller_cert_path`       | Path to the Teller certificate `.pem` file                                             | ✅      |
| `teller_key_path`        | Path to the Teller key `.pem` file                                                     | ✅      |
| `notion_custom_property` | Custom property in the format that Notion expects (see below)                          | ❌     |
| `notion_icon`            | What icon should the expense have in Notion (Example: 💳)                              | ❌     |
| `excluded`               | Expense name(s) that will not be written to Notion (Example: Walmart or Walmart,Amazon)| ❌     |




#### Installation

Pre-requisites:
- [Notion](https://notion.so) account
- A Notion Integration added to a desired database (see the [Notion guide](https://www.notion.so/help/create-integrations-with-the-notion-api))
- A [Teller](https://teller.io) account with a connected financial account (see the [Documentation](https://teller.io/docs))

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


More information on this format can be found [here](https://developers.notion.com/reference/database#database-property).

> NOTE: Use a Python code beautifier like [Code Beautify](https://codebeautify.org/python-formatter-beautifier) if you get stuck.
