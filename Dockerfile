FROM python:3.8-slim-buster

# Setup env
WORKDIR /opt

COPY app.py app.py
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

EXPOSE 8080

# We need root for some examples that write to PVs
USER 0

ENTRYPOINT [ "python3", "/opt/app.py" ]