```
╔╗╔┌─┐┌┬┐╔═╗╔╦╗╔═╗  ┌─┐┌─┐┬─┐┌─┐┌─┐┬─┐
║║║├┤  │ ║   ║║╠╣───├─┘├─┤├┬┘└─┐├┤ ├┬┘
╝╚╝└─┘ ┴ ╚═╝═╩╝╚    ┴  ┴ ┴┴└─└─┘└─┘┴└─
```
Before starting your container, be sure that your git configuration define autocrlf=false, then verify that files above use LF as endline:
- docker/django/Dockerfile
- docker/django/launcher.sh

This project is built on two containers using docker-compose, running the command above will build and run:
- a web container based on django which allow you to parse plot, kpi (sat, insitu, score) and product description files and write their content into database. It provides a REST api to exploit those data.
- a database container based on postgresql.

# Files management
## Folders / Subfolders
The django new commands developped in `apps/data_parser/management/commands/` are the following:
    - flush_database:
        Command to cleanup the database and create a new one to set all the tables using the file `universe_var_dtset.json` in root directory.
        The tables in the database are the following : Universe, Area, Variable, Product, Dataset, Subarea, Depth, PlotType, Stat, Plot
        The hierarchy of the tables in designed as follow:
        areas
        |_ universe\
        &nbsp;|_ variables\
        &nbsp;   &nbsp|_ datasets\
        &nbsp;   &nbsp;   &nbsp;|_ products\
        &nbsp;   &nbsp;   &nbsp;   &nbsp;|_ subareas\
        &nbsp;   &nbsp;   &nbsp;   &nbsp;   &nbsp;|_ depths\
        &nbsp;   &nbsp;   &nbsp;   &nbsp;   &nbsp; &nbsp;|_ stats\
        &nbsp;   &nbsp;   &nbsp;   &nbsp;   &nbsp; &nbsp, &nbsp;|_ plot_types

    - get_kpi_file:
        Command to download json files that will be injected in the database
    - process_files
        Command to process files to put informations in the database
    - update_cache
        Command to return a object containing all hierarchical avalaible filter

     All the functions are coded in the `apps/data_parser/services.py` file

##  Description of the database relations (django models)
    - class Area(models.Model)
    - class Universe(models.Model)
       areas = models.ManyToManyField(Area, related_name='universes')
    - class Variable(models.Model)
        universe = models.ForeignKey(Universe, related_name='variables', on_delete=models.CASCADE)
    - class Dataset(models.Model)
       variable = models.ForeignKey(Variable, related_name='datasets', on_delete=models.CASCADE)
    - class Product(models.Model)
      area = models.ForeignKey(Area, related_name='products', on_delete=models.CASCADE)
      datasets = models.ManyToManyField(Dataset, related_name='products')
    - class Subarea(models.Model)
      product = models.ForeignKey(Product, related_name='subareas', on_delete=models.CASCADE)
    - class Depth(models.Model):
      subareas = models.ManyToManyField(Subarea, related_name='depths')
    - class Stat(models.Model):
      depths = models.ManyToManyField(Depth, related_name='stats')
    - class PlotType(models.Model):
      stats = models.ManyToManyField(Stat, related_name='plot_types')

## Files processing
During files processing, the software will parse files in subdirectories above:
```
uploads
    |_ kpi
        |_ INSITU
            |_ INSITU_XXX_...
        |_ SAT
        |_ SKILL_SCORE
    |_ plot
    |_ text
```
All files under /kpi will be deleted after data extraction, so think to save a copy of them before running the process_files command.

## Filename
According to data type, some filename have to respect a precise nomenclature.
- KPI Satellite: 
```
area.json
```
- KPI Skill score: 
```
scores_YYYYMM.json
``` 
where MM is a two digit month and YYYY a four digits year.
- Plot: 
```
area_product_plottype_dataset_subarea_stat_depth.png
```
Be careful naming dataset, product, etc. each name should use "-" and not "_".

# Docker cheatsheet
```
docker-compose up                               // start all containers described into docker-compose.yml
docker ps                                       // list all runing containers
docker ps -a                                    // list all containers
docker stop $(docker ps -aq)                    // stop all running containers
docker container prune                          // remove all stopped containers
docker image ls                                 // list all images
docker rmi image_id                             // delete image image_id
docker exec -it container_name bash             // access to shell into container
```

# Setup backend
You can run this project both in development mode or production mode.
- Development mode use Django embeded server and load css, js, images, etc. from data_parser module.
- Production mode use uwsgi as appliation server, Nginx as web server server and load ressources from /static directory.

To switch between development or production release, just set variable PROD=True or False into docker-compose.yml

Start yours containers running:
```
docker-compose up
```
To access container through command line (quit with ctrl+d):
```
docker exec -it netcdf-parser_web_1 bash
```
To apply all migrations (setup database tables):
```
python manage.py migrate
```
To create an administrator who can access to django administration interface:
```
python manage.py createsuperuser
```
To collect all statics like css, js, images and make them avalaible in production mode:
```
python manage.py collectstatic
```
To setup database content from fresh install or flush all data and restart with a fresh database:
```
python manage.py flush_database
```
# How to use this project
## Through UI
This project expose two user interfaces.
The first one is an OpenAPI page. This page allow you to send some request to each avalaible 
endpoint with related HTTP method (POST, GET, etc.). It describes the arguments to pass when needed, the url to request for an external
call and an endpoint description.
The second one is an administration provide by Django Framework that allow you to interact with the database. To use it you need to
be logged as a superuser.

### OpenAPI Page
You can access to http://127.0.0.1:8000/swagger (if hosted just replace 127.0.0.1 by the DNS)

### Admin Page
You can access to http://127.0.0.1:8000/admin (if hosted just replace 127.0.0.1 by the DNS)

## Trough CLI
To use CLI reminds you have to access to comand line through your container running:

```
docker exec -it netcdf-parser_web_1 bash
```

- You can see avalaible commands using
```
python manage.py list
```
Note command into data_parser section, as follow:
```
python manage.py process_files
```
This command process all files under /uploads directory then preload cache files at the end.
If you need to update cache manually, after code update for example, you can force it running:
```
python manage.py update_cache
```

# Code structure
Two kind of interactions are possible: from HTTP web client or command line.
- Web client requests go through this path
```
HTTP RQ
|--> mysite/urls.py 
        -> apps/data_parser/urls.py 
            -> apps/data_parser/views.py
```
Class into views.py use openApi annotation to define swagger description, example, etc.

- Command line actions go through
```
CLI
|--> apps/data_parser/management/command_name.py
```

- Both entries call function from apps/data_parser/services.py
- This file contains several methods group by functionnality (parse files, extract data, calcul, etc.).
- Each function can use Models defined into apps/data_parser/models.py
- If a function return a model instance, it can use a Serializer defined into apps/data_parser/serializers.py
- Some dictonary used as return statement are not from Models so they are defined into apps/data_parser/classes.py
