import json
import os
import pickle
import time
from urllib.parse import urlencode

import praw as praw
import requests

MOD = "publicmodlogs"
FEED = '7e9b27126097f51ae6c9cd5b049af34891da6ba6'

def get_moderated_subreddits(mod=MOD):
    reddit = praw.Reddit()
    reddit.read_only = True
    redditor = reddit.redditor(mod)
    subreddits = list(redditor.moderated())
    return subreddits


def build_modlog_url(subreddit_name_unprefixed, feed=FEED, mod=MOD, limit=500, going_forward=True, before=None, after=None):

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


def get_modlog(subreddit_name_unprefixed, user_agent, feed=FEED, mod=MOD, limit=500, last_modaction_fname=None):
    modactions=list()

    s = requests.Session()
    s.headers.update({'User-Agent' : user_agent})

    going_forward, before, after=get_resume_data(subreddit_name_unprefixed, last_modaction_fname)

    do_break=False
    while not do_break:
        time.sleep(1)  # Sleep for one second to avoid going over API limits
        modlog_url = build_modlog_url(subreddit_name_unprefixed, feed, mod, limit, going_forward, before, after)
        # def get_modlog_once(modlog_url, modactions, going_forward, before, after):
        http = s.get(modlog_url)  # Make request to Reddit API
        if http.status_code != 200:  # This error handing is extremely basic.  Please improve.
            print(http.status_code)  # Print HTTP error status code to STDOUT
            break

        decode = json.loads(http.content)
        modactions.append(decode.copy())

        before, after, do_break = stopping_condition(decode, going_forward, before, after)

    modactions_flat = [k['data'] for j in modactions for i in j for k in i['data']['children']]
    return modactions_flat


def get_resume_data(subreddit_name_unprefixed, last_modaction_fname):
    # check if we already scraped the sub. if so, only get newer entries
    #see if a previous iteration left off somewhere; if so, we can pick up from there, and only get the incremental update. otherwise, we will get the entire log.
    start_positions = dict()
    if os.path.isfile(last_modaction_fname):
        print( 'reading previous data')
        with open(last_modaction_fname) as f:
            start_positions = pickle.load(f)
    going_forward = subreddit_name_unprefixed in start_positions
    before=None
    after=None
    if going_forward:
        before = start_positions[subreddit_name_unprefixed]

    return going_forward, before, after



if __name__ == '__main__':
    for subreddit in get_moderated_subreddits():
        print(build_modlog_url(subreddit))
