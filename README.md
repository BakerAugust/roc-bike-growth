# roc-bike-growth
Efficiently growing Rochester's bike networks


## Run using Docker desktop

There are many weird geospatial dependencies for `osmnx`, so the easiest thing to do is download docker desktop and run everything from a container. Once docker desktop is installed and running, you should be able to run the following:

*For Mac/Linux*

```
docker run --rm -it -p 8899:8899 -v "$PWD":/home/jovyan/work gboeing/osmnx:latest jupyter lab --ip '0.0.0.0' --port 8899 --no-browser
```

*For Windows*
```
docker run --rm -it -p 8899:8899 -v <absolute-path> gboeing/osmnx:latest jupyter lab --ip '0.0.0.0' --port 8899 --no-browser
```

You can then see jupyter lab at localhost:8899 in your browser. You may need to copy the token from your terminal as a password.
