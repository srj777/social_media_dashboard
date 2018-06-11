#!/usr/bin/env python
from gevent import monkey
monkey.patch_all()
from flask import Flask, url_for, render_template, send_from_directory,session,request
from flask_socketio import SocketIO, emit,join_room, leave_room,close_room, rooms, disconnect,Namespace,send
from threading import Lock
from flask import jsonify
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import API
from pathlib import Path
from textblob import TextBlob
from collections import Counter
import datetime
import pandas as pd
import json
import jinja2.exceptions
import re
import tweepy
import threading
import time

with open('config.json', 'r') as f:
    config = json.load(f)

#Variables that contains the user credentials to access Twitter API 
access_token = config['DEFAULT']['ACCESS_TOKEN']
access_token_secret = config['DEFAULT']['ACCESS_TOKEN_SECRET']
consumer_key = config['DEFAULT']['CONSUMER_KEY']
consumer_secret = config['DEFAULT']['CONSUMER_SECRET']


print(consumer_secret)






thread_lock = Lock()
simple_count_thread = None
tweet_collection_thread = None
tweet_collection_thread_event = threading.Event()
tweet_count = 0



def tokenize(s):
    return tokens_re.findall(s)
    
def preprocess(s, lowercase=True):
    tokens = tokenize(s)
    if lowercase:
        tokens = [token if emoticon_re.search(token) else token.lower() for token in tokens]
    return tokens
    
emoticons_str = r"""
    (?:
        [:=;] # Eyes
        [oO\-]? # Nose (optional)
        [D\)\]\(\]/\\OpP] # Mouth
    )"""    
    
regex_str = [
    emoticons_str,
        r'<[^>]+>', # HTML tags
        r'(?:@[\w_]+)', # @-mentions
        r"(?:\#+[\w_]+[\w\'_\-]*[\w_]+)", # hash-tags
        r'http[s]?://(?:[a-z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-f][0-9a-f]))+', # URLs
        r'(?:(?:\d+,?)+(?:\.?\d+)?)', # numbers
        r"(?:[a-z][a-z'\-_]+[a-z])", # words with - and '
        r'(?:[\w_]+)', # other words
        r'(?:\S)' # anything else
    ]

    
tokens_re = re.compile(r'('+'|'.join(regex_str)+')', re.VERBOSE | re.IGNORECASE)
emoticon_re = re.compile(r'^'+emoticons_str+'$', re.VERBOSE | re.IGNORECASE)    


app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='threading')


class TwitterClient(object):
    age_days = 1
    age_hours = 0
    age_mins = 0
    search_word = 'unifi'
    

    def __init__(self):
        '''
        Class constructor or initialization method.
        '''

        # attempt authentication
        try:
            # create OAuthHandler object
            self.auth = OAuthHandler(consumer_key, consumer_secret)
            # set access token and secret
            self.auth.set_access_token(access_token, access_token_secret)
            # create tweepy API object to fetch tweets
            self.api = tweepy.API(self.auth)
        except:
            print("Error: Authentication Failed")
            
    def clean_tweet(self, tweet):
        '''
        Utility function to clean tweet text by removing links, special characters
        using simple regex statements.
        '''
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())
 
    def get_tweet_sentiment(self, tweet):
        '''
        Utility function to classify sentiment of passed tweet
        using textblob's sentiment method
        '''
        # create TextBlob object of passed tweet text
        analysis = TextBlob(self.clean_tweet(tweet))
        # set sentiment
        if analysis.sentiment.polarity > 0:
            return 'positive'
        elif analysis.sentiment.polarity == 0:
            return 'neutral'
        else:
            return 'negative'
            
    def update_all(self):
        
        # empty list to store parsed tweets
        tweets = []
        now = datetime.datetime.now()
        break_flag = False   
        global socketio
        global tweet_collection_thread
        
        try:
        
            # create an empty dataframe
            all_tweets = pd.DataFrame(columns=['id',
                                               'source',
                                               'user_id',
                                               'user_name',
                                               'user_screen_name',
                                               'user_location',
                                               'user_followers_count',
                                               'user_friends_count',
                                               'user_timestamp',
                                               'user_statuses_count',
                                               'user_lang',
                                               'user_profile_image',
                                               'place_id',
                                               'place_name',
                                               'place_country_code',
                                               'place_country',
                                               'tweet_date',
                                               'text',
                                               'sentiment'])
            
            page_count = 1

            for page in tweepy.Cursor(self.api.search, q=self.search_word,count=100).pages():
                if tweet_collection_thread_event.is_set():
                    socketio.emit('st_msg',{'text':'Search stopped in between on user request'},namespace='/all')
                    return
                # rt_status = self.api.rate_limit_status()
                # limit = rt_status['resources']['search']['/search/tweets']['limit']
                # remaining = rt_status['resources']['search']['/search/tweets']['remaining']
                # reset_time = rt_status['resources']['search']['/search/tweets']['reset']
                # rst_time = datetime.datetime.fromtimestamp(reset_time).strftime('%Y-%m-%d %H:%M:%S')
                # rate_limit_status = {'limit':limit,'remaining':remaining,'rst_time':rst_time,'page_count':page_count}
                rate_limit_status = {'limit':0,'remaining':0,'rst_time':0,'page_count':page_count}
                
                socketio.emit('rate_limit',rate_limit_status,namespace='/all')
                
                page_count += 1
                
                for tweet in page:

                    parsed_tweet = {}
     
                    # saving text of tweet
                    parsed_tweet['id'] = tweet.id
                    parsed_tweet['source'] = tweet.source
                    parsed_tweet['user_id'] = tweet.user.id
                    parsed_tweet['user_name'] = tweet.user.name
                    parsed_tweet['user_screen_name'] = tweet.user.screen_name
                    parsed_tweet['user_location'] = tweet.user.location
                    parsed_tweet['user_followers_count'] = tweet.user.followers_count
                    parsed_tweet['user_friends_count'] = tweet.user.friends_count
                    parsed_tweet['user_timestamp'] = tweet.user.created_at
                    parsed_tweet['user_statuses_count'] = tweet.user.statuses_count
                    parsed_tweet['user_lang'] = tweet.user.lang
                    parsed_tweet['user_profile_image'] = tweet.user.profile_image_url
                    if tweet.place != None:
                        parsed_tweet['place_id'] = tweet.place.id
                        parsed_tweet['place_name'] = tweet.place.full_name
                        parsed_tweet['place_country_code'] = tweet.place.country_code
                        parsed_tweet['place_country'] = tweet.place.country
                    else:
                        parsed_tweet['place_id'] = None
                        parsed_tweet['place_name'] = None
                        parsed_tweet['place_country_code'] = None
                        parsed_tweet['place_country'] = None
                    parsed_tweet['tweet_date'] = tweet.created_at
                    parsed_tweet['text'] = tweet.text
                    parsed_tweet['sentiment'] = self.get_tweet_sentiment(tweet.text)
                    
                    tweets.append(parsed_tweet)

                if len(tweets) < 1:
                    print('Zero tweets')
                    socketio.emit('st_msg',{'text':'Zero tweets with this search'},namespace='/all')
                    return None,None
                else:
                    tweet_df = pd.DataFrame.from_records(tweets)
                    if min(tweet_df['tweet_date']) <= (now - datetime.timedelta(days=self.age_days,hours=self.age_hours)):              
                        tweet_df = tweet_df[tweet_df['tweet_date'] > (now - datetime.timedelta(days=self.age_days,hours=self.age_hours))]
                        all_tweets = all_tweets.append(tweet_df, ignore_index=True)
                        if all_tweets.shape[0] == 0:
                            socketio.emit('st_msg',{'text':'Zero tweets within 1 day... still providing older tweets'},namespace='/all')
                            tweet_df = pd.DataFrame.from_records(tweets)
                            all_tweets = all_tweets.append(tweet_df, ignore_index=True)
                        break_flag = True
                    else:
                        all_tweets = all_tweets.append(tweet_df, ignore_index=True)
                        
                if break_flag:
                    break    

                if page_count >= 10:
                    socketio.emit('st_msg',{'text':'More than 1000 tweets in day. Stopping...'},namespace='/all')
                    break

                if tweet_collection_thread_event.is_set():
                    socketio.emit('st_msg',{'text':'Search stopped in between on user request'},namespace='/all')
                    tweet_collection_thread = None
                    return
                    
            total_tweets = all_tweets.shape[0]
            socketio.emit('total_tweets',{'data':total_tweets},namespace='/all')
            
            loc_tweets = all_tweets[all_tweets['place_id'].notnull()]
            loc_tweets['address'] = loc_tweets[['place_name', 'place_country']].apply(lambda x: ','.join(x), axis=1)
            loc_tweets['count'] = 1
            
            socketio.emit('tweet_locations',loc_tweets[['address','count']].to_json(orient='records'),namespace='/all')
            
            total_tweet_loc = loc_tweets.shape[0]
            
            socketio.emit('st_msg',{'text': str(total_tweet_loc) + ' out of ' + str(total_tweets) + ' tweets have location info' },namespace='/all')
            
            all_tweets = all_tweets.sort_values(by=['tweet_date'],ascending=False)
            
            socketio.emit('recent_tweets',all_tweets.loc[[0,1,2,3,4],['user_name','user_profile_image','text','user_screen_name']].to_json(orient='records'),namespace='/all')

            influencers = all_tweets[['user_name','user_profile_image','user_followers_count','user_location','user_screen_name']]
            influencers = influencers.drop_duplicates(['user_name'])
            influencers = influencers.sort_values(by=['user_followers_count'],ascending=False).reset_index(drop=True)
            top_users = influencers.iloc[[0,1,2,3,4]]
            socketio.emit('top_users',top_users.to_json(orient='records'),namespace='/all')
            
            
            pos_tweets = all_tweets[all_tweets['sentiment'] == 'positive'].shape[0]
            neg_tweets = all_tweets[all_tweets['sentiment'] == 'negative'].shape[0]
            neu_tweets = all_tweets[all_tweets['sentiment'] == 'neutral'].shape[0]
            
            pos_sentiment = pos_tweets*100/total_tweets
            neg_sentiment = neg_tweets*100/total_tweets
            neu_sentiment = neu_tweets*100/total_tweets
            
            sentiment_perc = [{'sentiment':'positive','percentage':pos_sentiment},
                              {'sentiment':'negative','percentage':neg_sentiment},
                              {'sentiment':'neutral','percentage':neu_sentiment}]
            
            
            socketio.emit('sentiments',json.dumps(sentiment_perc),namespace='/all')
            
            count_all = Counter()
            
            for item in all_tweets['text'].tolist():
                terms_all = re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", item).split()
                count_all.update(terms_all)
                
            d = dict(count_all)
            word_freq_df = pd.DataFrame(list(d.items()), columns=['text','weight'])
            socketio.emit('word_cloud',word_freq_df.to_json(orient='records'),namespace='/all')
            
            tweet_collection_thread = None
            return
                        
        except tweepy.TweepError as e:
            print(str(e))
            
    
            

tt_client = TwitterClient()


count = 0
def background_thread_simple_count():

    global count
    while True:
        socketio.sleep(3)
        count += 1
        socketio.emit('simple_cnt',
                      {'data': 'Server alive !!!', 'count': count},
                      namespace='/all')
        if count >= 100000:
            count = 0

def background_tweet_collection():
    global tt_client
    tt_client.update_all()
    
            
@app.route('/')
def index():
    return render_template('index.html',async_mode=socketio.async_mode)

@app.route('/<pagename>')
def admin(pagename):
    return render_template(pagename+'.html')

@app.route('/<path:resource>')
def serveStaticResource(resource):
    return send_from_directory('static/', resource)

@app.route('/test')
def test():
    return '<strong>It\'s Alive!</strong>'

@app.errorhandler(jinja2.exceptions.TemplateNotFound)
def template_not_found(e):
    return not_found(e)

@app.errorhandler(404)
def not_found(e):
    return '<strong>Page Not Found!</strong>',     0    
    
    
@socketio.on('connect', namespace='/all')
def all_connect():
    emit('conn_response', {'data': 'Connected'})
    global simple_count_thread
    with thread_lock:
        if simple_count_thread is None:
            simple_count_thread = socketio.start_background_task(target=background_thread_simple_count)    
    
@socketio.on('disconnect', namespace='/all')
def all_disconnect():
    print('Client disconnected')    
    
    
@socketio.on_error_default  # handles all namespaces without an explicit error handler
def default_error_handler(e):
    print('Some websocket socket error !!!' + e)    
    
    
@socketio.on('my_ping', namespace='/all')
def all_ping_pong():
    emit('my_pong')
    
@socketio.on('search', namespace='/all')
def search_word(data):
    emit('search_request_received',{'data':'search request received for : ' + data['search_word']})
    global tweet_collection_thread
    tt_client.search_word = data['search_word']
    with thread_lock:
        if tweet_collection_thread is None:
            tweet_collection_thread = socketio.start_background_task(target=background_tweet_collection)
            print('new search thread started')
        else:
            print('can not get new thread for search')
    
@socketio.on('stop_request', namespace='/all')
def all_stop_request():
    print('stop request received !')
    global tweet_collection_thread
    global tweet_collection_thread_event
    if tweet_collection_thread is not None:
        tweet_collection_thread_event.set()
        emit('st_msg',{'text':'Waiting for previous tasks to finish'})
        tweet_collection_thread.join()
        tweet_collection_thread = None
        emit('st_msg',{'text':'Previous task stopped'})
        tweet_collection_thread_event.clear()
    else:
        emit('st_msg',{'text':'No tasks found to stop'})
    
    

    
if __name__ == '__main__':
    socketio.run(app,host='0.0.0.0',port=9000, debug=True)    
    
