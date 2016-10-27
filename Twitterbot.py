#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tweepy, time, sys

argfile = str(sys.argv[1])


CKEY = ''  
CSECRET = ''  
AKEY = ''  
AECRET = ''  
auth = tweepy.OAuthHandler(CKEY, CSECRET)
auth.set_access_token(AKEY, ASECRET)
api = tweepy.API(auth)

filename = open(argfile, 'r')
f = filename.readlines()
filename.close()

for line in f:
    api.update_status(status=line)
    time.sleep(45)  # Tweet every 45 seconds
