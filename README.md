```
╔╗╔┌─┐┌┬┐╔═╗╔╦╗╔═╗  ┌─┐┌─┐┬─┐┌─┐┌─┐┬─┐
║║║├┤  │ ║   ║║╠╣───├─┘├─┤├┬┘└─┐├┤ ├┬┘
╝╚╝└─┘ ┴ ╚═╝═╩╝╚    ┴  ┴ ┴┴└─└─┘└─┘┴└─
```
# Start container
```
docker-compose up
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