# XCo - XPS Cloud API // Version 2


## Django + Docker

### Getting Started.

#### Get Docker Running

    docker-compose up

    This will get your docker containers up and running, but things won't work yet. CTRL-C to stop, then follow the next steps.


#### Create .env file in backend/xps_cloud/settings/ folder

    DEBUG=True
    DATABASE_URL='postgres://postgres:postgres@db/xps'
    SLAVE1_URL='postgres://postgres:postgres@db/xps'
    SLAVE2_URL='postgres://postgres:postgres@db/xps'
    REDIS_MASTER_HOST='localhost'
    REDIS_SLAVE_HOST='localhost'


#### Start Docker containers.

    docker-compose start    # to start the containers
    docker-compose logs -f  # to watch the logs


#### Create a database

    sh docker-shell.sh db
    su - postgres
    psql
    create database xps;
    create database xps_test;
    \q
    exit


#### Getting a shell prompt on your web server

    sh docker-shell.sh web

    The shell that gets opened is the docker container shell + the pipenv shell. So two 'exit' commands are needed to actually exit back to your host machine.


#### Inside the docker(web) shell.. migrate

    python manage.py migrate  # to run the initial migrations


### PyTest

To run pytest unit tests (inside of the docker web container)

    sh web_shell.sh
    pytest xps_cloud/tests/ apps/

