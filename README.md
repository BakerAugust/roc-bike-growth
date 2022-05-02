# roc-bike-growth
Efficiently growing Rochester's bike networks. For the writeup on our work, checkout `roc-bike-growth writeup.pdf`.


## Using the Docker Environment

There are many weird geospatial dependencies for `osmnx`, so the easiest thing to do is download docker desktop and run everything from a container. Once docker desktop is installed and running, you should be able to run the following:

*For Mac/Linux*

```
docker run --rm -it -p 8899:8899 -v "$PWD":/home/jovyan/work gboeing/osmnx:latest jupyter lab --ip '0.0.0.0' --port 8899 --no-browser
```

*For Windows (untested)*
```
docker run --rm -it -p 8899:8899 -v "%cd%":/home/jovyan/work gboeing/osmnx:latest jupyter lab --ip '0.0.0.0' --port 8899 --no-browser
```

You can then see jupyter lab at localhost:8899 in your browser. You may need to copy the token from your terminal as a password.


## Running tests

Tests are written for use with `pytest`.

Run with the following command:

`python3 -m pytest`



