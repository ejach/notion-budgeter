### notion-budgeter
[![PyPI](https://img.shields.io/pypi/v/plaid-python?logo=python&label=plaid-python&style=flat-square&color=FFD43B)](https://pypi.org/project/plaid-python/)
[![PyPI](https://img.shields.io/pypi/v/schedule?logo=python&label=schedule&style=flat-square&color=FFD43B)](https://pypi.org/project/schedule/)
[![PyPI](https://img.shields.io/pypi/v/SQLAlchemy?logo=python&label=SQLAlchemy&style=flat-square&color=FFD43B)](https://pypi.org/project/SQLAlchemy/)
[![PyPI](https://img.shields.io/pypi/v/requests?logo=python&label=requests&style=flat-square&color=FFD43B)](https://pypi.org/project/requests/)

Keeps a given Notion database up to date with transactions using Plaid.

#### docker-compose.yml
```yml
version: '3.7'
services:
  notion_budgeter:
    image: notion_budgeter
    container_name: ghcr.io/ejach/notion_budgeter
    environment:
      - access_token=<access_token>
      - client_id=<plaid_client_id>
      - secret=<plaid_secret>
      - base_url=<pipedream_base_url>
      - data_dir=<path_to_data>
    volumes:
      - /path/to/data:/path/to/data
    restart: unless-stopped
```
