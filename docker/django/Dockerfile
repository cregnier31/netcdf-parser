FROM python:3.7

RUN apt-get update -y
# Build and production mode
RUN apt-get install python3.7-dev -y
RUN apt-get install build-essential -y
RUN apt-get install dos2unix -y
RUN apt-get install nginx -y 

RUN mkdir /code
COPY . /code
WORKDIR /code

RUN pip install -r requirements.txt

COPY ./docker/nginx/mysite_nginx.conf /etc/nginx/conf.d/default.conf

RUN set -e; \
    find . -type f -print0 | xargs -0 dos2unix

CMD ["/bin/bash", "docker/django/launcher.sh"]