FROM python:3.10
COPY requirements.txt .
RUN python -m pip install -r requirements.txt
COPY *.py ./
COPY input.json .
COPY input.schema.json .

ENTRYPOINT [ "python", "main.py" ]
