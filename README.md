# i-SAS_Interface
Implementation of the interface for i-SAS

## 1. Clone
```shell
$ git clone git@github.com:i-SAS/i-SAS_Interface.git
$ cd i-SAS_Interface
```

## 2. Docker build & run
Copy and modify `.env` according to your environment before building the docker image.
```shell
$ cp .env{.example,}
```

To run the test, you need to control access to the X server by the following command in the host.
```shell
$ xhost +localhost
```
Note that while this command can be convenient for local access, it can also pose security risks if used indiscriminately, as it allows any local user or application to interact with the X server.

Now, you can build the image.
```shell
$ DOCKER_BUILDKIT=1 docker build --ssh default . -t isas_interface
$ docker compose run --rm package
```

## 3. Commands
### Download data
```shell
poetry run isas_download
```

### Add package
Modify `pyproject.toml` and execute
```shell
poetry lock
```
Note that you need to run ssh-agent in the container before the command, and rebuild the image after the command.

### Check coding conventions
```shell
flake8
```

### Run test
```shell
python -m unittest
```
