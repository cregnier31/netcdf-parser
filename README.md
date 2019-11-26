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
python manage.py loaddata univers_variable_dataset.json
```
# Use your container
## Through UI
You can access to http://127.0.0.1:8000/swagger
## Trough CLI
You can see avalaible commands using
```
docker exec -it netcdf-parser_web_1 bash
python manage.py process_files
```