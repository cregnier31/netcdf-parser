FROM python:3.7-slim

RUN mkdir /code
COPY . /code
WORKDIR /code

RUN apt-get update -y
RUN apt-get install python3.7-dev  -y
RUN apt-get install build-essential -y
RUN apt-get install nginx -y 

RUN pip install -r requirements.txt

COPY ./docker/nginx/mysite_nginx.conf /etc/nginx/conf.d/default.conf

CMD ["/bin/bash", "docker/django/launcher.sh"]