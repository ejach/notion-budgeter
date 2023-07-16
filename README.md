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
    container_name: ghcr.io/ejach/notion-budgeter
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
#### Installation
> NOTE: What you do with the `POST` request data is up to you. I ended up using a [Pipedream](https://pipedream.com) workflow to interact with Notion to keep it simple. Any plugin that receives `POST` requests and interacts with Notion will work fine. Likewise, anything that is demonstrated in this guide can be customized to fit your needs.

Pre-requisites:
- [Notion](https://notion.so) account
- A Notion database with a Pipedream connection (see the [Notion guide](https://www.notion.so/help/guides/connecting-tools-to-notion))
- [Pipedream](https://pipedream.com) account
- [Plaid](https://dashboard.plaid.com/signup) account with a [Development API Token](https://plaid.com/docs/quickstart/glossary/#development) and an account `client_id` and `secret` from a connected financial account (see the [Quickstart](https://github.com/plaid/quickstart) repository)

____

##### Step 1:

Log into [Pipedream](https://pipedream.com) and create a new workflow.


> NOTE: No matter what you do with the data, the first step in any workflow should consume the `POST` requests


Select the `New Webhook / HTTP Requests` trigger and select `HTTP Body Only` 


<img width="1440" alt="Screenshot 2023-07-16 at 1 49 36 PM" src="https://github.com/ejach/notion-budgeter/assets/42357644/879ca940-a7f0-424b-965f-e20d6b5cc341">

##### Step 2:

Add a new trigger by hitting the `+` and search for `Notion` 


Under the `Notion Actions` select `Create a Page from Database` 


<img width="1438" alt="Screenshot 2023-07-16 at 2 03 43 PM" src="https://github.com/ejach/notion-budgeter/assets/42357644/c4e2f712-5ef3-4c19-9b8b-6f2cb527fa9f">

After you create this workflow, connect your Notion account to Pipedream, and you will see your databases under `Parent Database ID`:

<img width="1437" alt="Screenshot 2023-07-16 at 2 13 56 PM" src="https://github.com/ejach/notion-budgeter/assets/42357644/10944460-8cde-4b89-8509-2ab1081efb37">


#### Step 3

Select the `Property Types` you wish to populate with the `POST` data

<img width="1440" alt="Screenshot 2023-07-16 at 2 19 30 PM" src="https://github.com/ejach/notion-budgeter/assets/42357644/20fded6a-671c-4444-bd36-9d6bc5de7645">

To access the data from the `POST` request, use the format `{{steps.trigger.event.$VAR}}`

The variables to be retrieved from the request are:
- `{{steps.trigger.event.expense}}` - Expense name
- `{{steps.trigger.event.amount}}` - Expense amount
- `{{steps.trigger.event.date}}` - Date posted

After everything is populated and the workflow works correctly, hit the `Deploy` button, and copy the link to be used when setting up the environment:

<img width="1249" alt="Screenshot 2023-07-16 at 2 29 32 PM" src="https://github.com/ejach/notion-budgeter/assets/42357644/3518207c-045d-495b-aeba-63baefabb472">

Go crazy 🤙🏻
