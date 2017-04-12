import tweepy
import json

class IncNotify():

    def __init__(self):
        #
        # twitter_auth.json File Format
        #
        #{
        #	"consumer_key" :  "blah",
        #	"consumer_secret" : "blah",
        #	"access_token" : "blah",
        #	"access_secret" : "blah"
        #}

        twitter_auth = json.loads(open('twitter_auth.json').read())    
        # Configure auth for twitter        
        auth = tweepy.OAuthHandler(twitter_auth['consumer_key'], twitter_auth['consumer_secret'])
        auth.set_access_token(twitter_auth['access_token'], twitter_auth['access_secret'])

        self.api = tweepy.API(auth)

        ## TODO handle failure
        print ("Twitter output enabled")

    def notify(self, img, level):

        # TODO img is correct format.
        if self.api is None or img is None or level == 0:
            return None
    
        msg = "The incubator monitor has detected a gecko hatching.  Did I get it right?"
    
        if level <= 1:
            self.api.send_direct_message(user="namezmud", text=msg)
        else:
            path = img.output_path
            if not path:
                path = img.path
            self.api.update_with_media(path, msg)
             
        print("SEND!!!! " + img.getShortname())
