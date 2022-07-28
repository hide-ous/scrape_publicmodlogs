
get public modlogs for subreddits moderated by u/[publicmodlogs](reddit.com/r/publicmodlogs/)

## prerequisites
- access to the [Reddit API](https://github.com/reddit-archive/reddit/wiki/OAuth2-Quick-Start-Example#first-steps)
- a `praw.ini` [configuration file](https://praw.readthedocs.io/en/stable/getting_started/configuration/prawini.html). a template is available in this repository as `praw.ini.example`
- either docker or python 3.8+

## to run


### pulling from dockerhub
you should mount your praw.ini file and a folder where to share the scraped modlog
data with the host, respectively at the `/praw.ini` and `/data` mount points. 
please spare yourseld headaches by providing absolute paths.
```shell
docker run -d --name pymodlogs \
    --mount type=bind,source=/absolute/path/to/praw.ini,target=/praw.ini \ 
    -v /absolute/path/to/data/folder:/data \
    hide0us/pymodlogs:latest
```

### building the docker image locally
```shell
git clone https://github.com/hide-ous/scrape_publicmodlogs.git
cd scrape_publicmodlogs
docker build -t pymodlogs . 
docker run -d --name pymodlogs \
    --mount type=bind,source=/absolute/path/to/praw.ini,target=/praw.ini \ 
    -v /absolute/path/to/data/folder:/data \
    pymodlogs
```

### running the python scripts directly
clone the repository
```shell
git clone https://github.com/hide-ous/scrape_publicmodlogs.git
cd scrape_publicmodlogs
```
(recommended) use a new virtual environment, e.g.,
```shell
python -m venv venv
source venv/bin/activate 
```
then install dependencies and run
```shell
pip install -r requirements.txt
python -u main.py
```