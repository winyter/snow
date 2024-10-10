FROM python:3.10.14-slim

WORKDIR /app

RUN mkdir -p /tmp/snow/deps \
  && echo 'export PYTHONPATH=$PYTHONPATH:/app' >> ~/.bashrc

RUN pip3 install -r /tmp/snow/deps/requirements.txt

COPY ./config_center/ /app/

RUN rm -rf /tmp/snow

EXPOSE 9791

CMD python3 /app/snow_cc.py