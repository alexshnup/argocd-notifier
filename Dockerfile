FROM python:3.10-slim

RUN pip install flask requests pyyaml kubernetes

WORKDIR /app
COPY . .

RUN mkdir /data
VOLUME /data

ENV CONFIG_PATH /app/config.yaml

CMD ["python3", "notifier.py"]
