from time import sleep

from notion_budgeter.notion_budgeter.notion_budgeter import send_to_notion
from schedule import every, run_pending

if __name__ == '__main__':
    send_to_notion()
    # every().minute.do(send_to_notion)
    #
    # while True:
    #     run_pending()
    #     sleep(1)
