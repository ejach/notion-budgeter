FROM python:3.8-alpine

WORKDIR /notion_budgeter

ENV PYTHONUNBUFFERED=1

RUN ln -sf /usr/share/zoneinfo/America/New_York /etc/localtime && \
    echo "America/New_York" > /etc/timezone

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "notion_budgeter"]
