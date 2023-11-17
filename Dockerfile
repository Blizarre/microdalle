FROM python:3.11-slim

WORKDIR /app/

RUN useradd web -s /bin/false

ADD requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

ADD index.html inprogress.gif server.py  /app/

EXPOSE 8000

USER web

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "-w", "4", "-t", "120", "server:app"]
