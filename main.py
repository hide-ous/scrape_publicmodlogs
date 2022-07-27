import json
import os
import pathlib
import pickle
import time
from urllib.parse import urlencode

import praw as praw
import requests
import schedule as schedule
from tqdm import tqdm
from ratelimit import limits, sleep_and_retry

MOD = "publicmodlogs"
FEED = '7e9b27126097f51ae6c9cd5b049af34891da6ba6'
CALLS=1 # rate limiting
PERIOD=1 # rate limiting
MODACTIONS_PATH_TEMPLATE= os.path.join('data', '{subreddit}.njson')
RESUME_PATH=os.path.join('data', 'resume.pkl')

def get_reddit(config_interpolation='basic'):
    reddit = praw.Reddit(config_interpolation=config_interpolation)
    reddit.read_only = True
    return reddit

def get_moderated_subreddits(reddit, mod=MOD):
    redditor = reddit.redditor(mod)
    subreddits = list(redditor.moderated())
    return subreddits


def build_modlog_url(subreddit_name_unprefixed, feed=FEED, mod=MOD, limit=500, going_forward=False, before=None, after=None):

    base_url=f'https://www.reddit.com/r/{subreddit_name_unprefixed}/about/log/.json?'
    params = dict(limit=limit, user=mod, feed=feed)
    if going_forward and before:
        params['before']=before
    elif after:
        params['after']=after
    url = base_url+urlencode(params)
    return url


def stopping_condition(decode, going_forward, before, after):
    do_break=False
    # stopping conditions
    if not len(decode['data']['children']):
        do_break=True
    if going_forward:
        if before == decode['data']['children'][0]['data']['id']:
            do_break=True
        # the modaction of the most recent element
        before = decode['data']['children'][0]['data']['id']
        if not before:
            do_break=True
    else:
        if after == decode['data']['after']:
            do_break=True
        # the modaction of the least recent element
        after = decode['data']['after']
        if not after:
            do_break=True
    return before, after, do_break


@sleep_and_retry
@limits(calls=CALLS, period=PERIOD)
def __get_one_modlog_page(s, modlog_url, modactions, going_forward, before, after):
    http = s.get(modlog_url)  # Make request to Reddit API
    if http.status_code != 200:  # This error handing is extremely basic.  Please improve.
        print(http.status_code)  # Print HTTP error status code to STDOUT
        do_break = True
    else:
        decode = json.loads(http.content)
        modactions.extend([k['data'] for k in decode['data']['children']])
        before, after, do_break = stopping_condition(decode, going_forward, before, after)
    return before, after, do_break # caller should check do_break right after the function call


def get_modlog(subreddit_name_unprefixed, user_agent, feed=FEED, mod=MOD, limit=500, last_modaction_fname=RESUME_PATH):
    modactions=list()

    s = requests.Session()
    s.headers.update({'User-Agent' : user_agent})
    after=None
    going_forward, before=get_resume_data(subreddit_name_unprefixed, last_modaction_fname)

    do_break=False
    while not do_break:
        modlog_url = build_modlog_url(subreddit_name_unprefixed, feed, mod, limit, going_forward, before, after)
        before, after, do_break = __get_one_modlog_page(s, modlog_url, modactions, going_forward, before, after)
    return modactions


def read_resume_data(dest_file):
    start_positions=dict()
    if os.path.isfile(dest_file):
        print( 'reading previous data')
        with open(dest_file) as f:
            start_positions = pickle.load(f)
    return start_positions


def store_resume_data(modactions, subreddit_name_unprefixed, dest_file=RESUME_PATH):
    start_positions = read_resume_data(dest_file)
    last_utc = max(action['created_utc'] for action in modactions)
    start_positions.update({subreddit_name_unprefixed:last_utc})
    create_dirs(dest_file)
    with open(dest_file, 'wb') as f:
        pickle.dump(start_positions, f)


def get_resume_data(subreddit_name_unprefixed, dest_file=RESUME_PATH):
    # check if we already scraped the sub. if so, only get newer entries
    #see if a previous iteration left off somewhere; if so, we can pick up from there, and only get the incremental update. otherwise, we will get the entire log.
    start_positions = read_resume_data(dest_file)
    going_forward = subreddit_name_unprefixed in start_positions
    before=None
    if going_forward:
        before = start_positions[subreddit_name_unprefixed]
    return going_forward, before


def create_dirs(dest_file):
    if not os.path.exists(dest_file):
        pathlib.Path(os.path.dirname(dest_file)).mkdir(parents=True, exist_ok=True)

def store_modlogs(modactions, subreddit_name_unprefixed, fpath_template=MODACTIONS_PATH_TEMPLATE):
    dest_file= fpath_template.format(subreddit=subreddit_name_unprefixed)
    create_dirs(dest_file)
    with open(dest_file, 'a+', encoding='utf8') as f:
        f.write('\n'.join(map(json.dumps, modactions)) + '\n')

def get_a_scrapin():
    reddit = get_reddit()
    user_agent = reddit.config.user_agent
    subreddits = list(get_moderated_subreddits(reddit))
    for subreddit in (pbar := tqdm(subreddits)):
        pbar.set_description("Processing %s" % subreddit)
        modactions = get_modlog(subreddit, user_agent)
        store_modlogs(modactions, subreddit)
        store_resume_data(modactions, subreddit)

if __name__ == '__main__':
    #scrape once
    get_a_scrapin()
    schedule.every().hour.do(get_a_scrapin)
    #keep on scraping forever
    while True:
        schedule.run_pending()
        time.sleep(60) # wait one minute