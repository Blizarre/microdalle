FROM python:3.11-slim

WORKDIR /app/

ADD index.html inprogress.gif server.py requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

RUN useradd web -s /dev/null

USER web

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "-w", "4", "-t", "120", "server:app"]
