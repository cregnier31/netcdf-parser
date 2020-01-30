#!/bin/bash #
echo "$PROD"

if [ "$PROD" = "True" ] || [ "$PROD" = "1" ] 
then 
    echo "Let's build in production mode (debug = False, server = Nginx)"
    /etc/init.d/nginx start 
    uwsgi --socket :8001 --wsgi-file ./mysite/wsgi.py 
else 
    echo "Let's build in dev mode (debug = True or False, server = Django)"
    python manage.py runserver 0.0.0.0:8000 
fi