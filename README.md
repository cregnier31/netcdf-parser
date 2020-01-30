```
╔╗╔┌─┐┌┬┐╔═╗╔╦╗╔═╗  ┌─┐┌─┐┬─┐┌─┐┌─┐┬─┐
║║║├┤  │ ║   ║║╠╣───├─┘├─┤├┬┘└─┐├┤ ├┬┘
╝╚╝└─┘ ┴ ╚═╝═╩╝╚    ┴  ┴ ┴┴└─└─┘└─┘┴└─
```
# Start container
```
docker-compose up
```
# Setup database
```
docker exec -it netcdf-parser_web_1 bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
python manage.py flush_database
```
# Use your container
## Through UI
You can access to http://127.0.0.1:8000/swagger (the OpenAPI page) and http://127.0.0.1:8000/admin (for database administration)
## Trough CLI
You can see avalaible commands using
```
docker exec -it netcdf-parser_web_1 bash
python manage.py process_files
```
Cache may be automaticaly update after files processing, but if needed you can force it running:
```
docker exec -it netcdf-parser_web_1 bash
python manage.py update_cache
```