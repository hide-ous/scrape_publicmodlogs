
get public modlogs for subreddits moderated by u/publicmodlogs

## to run

```shell
docker run -d --name pymodlogs \
    --mount type=bind,source=/absolute/path/to/praw.ini,target=/praw.ini \ 
    -v /absolute/path/to/data/folder:/data \
    hide0us/pymodlogs:latest
```


