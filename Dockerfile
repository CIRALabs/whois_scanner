FROM python:3.10
COPY requirements.txt .
RUN python -m pip install -r requirements.txt
COPY input.schema.json .
COPY *.py ./
COPY input.json .

ENTRYPOINT [ "python", "main.py" ]
