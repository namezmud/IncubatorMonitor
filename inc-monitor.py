#!/home/pi/.virtualenvs/cv/bin/python3
import argparse
import datetime
import imutils
import time
import cv2
import matplotlib
import numpy
import os
import re
import json
import incimagedetect
import picamera
import tweepy
from enum import Enum
from picamera import PiCamera
from time import sleep

# arg parser
ap = argparse.ArgumentParser()
ap.add_argument("-d", "--dir", default="ref/", help="Directory containing image files")
ap.add_argument("-a", "--min_area", type=int, default=2500, help="Minimum size in pixels of a motion area.")
ap.add_argument("-t", "--thresh", type=int, default=30, help="Intensity difference threshold.")
ap.add_argument("-o", "--output", default="output/", help="Output directory")
ap.add_argument("-c", "--change", type=int, default=50000, help="Pixel Change to set new reference")
ap.add_argument("-n", "--tweet", nargs='?', const='Y', default='N', help="enable twitter")
    
#ap.add_argument("-p", "--pics", default="output/", help="")
ap.add_argument("-l", "--live", nargs='?', const='Y', default='N', help="Use live Cam")

args = vars(ap.parse_args())

twitter = None

def config_twitter():
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

    api = tweepy.API(auth)
    print ("Twitter output enabled")

    return api

twitter_DM = False
    
# Function to send DM via twitter when alert occurs
def announce(img):
    global twitter_DM
    global twitter

    if twitter is None or img.getStatus() != DetectMultiFrame.DetectValue.Found:
        return None
    
    msg = "The incubator monitor has detected a gecko hatching.  Did I get it right?"
    
    if twitter_DM:
        twitter.send_direct_message(user="namezmud", text=msg)
    else:
        path = img.output_path
        if not path:
            path = img.path
        twitter.update_with_media(path, msg)
         
    print("SEND!!!! " + img.getShortname())

live_mode = args['live'] != 'N'

if live_mode:
    print("In live mode")
else:
    print("In replay mode")
    if args.get("dir", None) is None:
       print("No dir set")
       exit
    dir = args["dir"]
    if os.path.isdir(dir):
        print("Using dir ", dir)
    else:
        print ("Could not find ", dir)
        exit

min_area = args.get("min_area")
threshold = args.get("thresh")
changeThreshold = args.get("change")
reset_interval = 60
announce_threshold = 3


pics = True
results = {}
results['files'] = {}

print("min_area", min_area)
print("thresh", threshold)


if args.get("tweet") == 'Y':
    twitter = config_twitter()

if live_mode:
    files = []
else:
    files = os.listdir(dir)
    files.sort()
    print(len(files), "files found")

ref = None
periodic_reset = 0
announced = False

results['settings'] = {}
results['settings']['threshold'] = threshold
results['settings']['min_size'] = min_area
results['settings']['change_threshold'] = changeThreshold
results['settings']['files'] = len(files)  

def write_results(results):
    with open(args.get("output") +'/a_results.json', 'w') as outfile:
        json.dump(results, outfile)
    
def process_image(f, history, write_output):
    global ref
    global periodic_reset
    global announced
    
    if ref is None:
        ref = DetectMultiFrame.DetectFrame(f)
        print("New reference ", ref.getShortname())
        periodic_reset = 0
        return

    img = DetectMultiFrame.DetectFrame(f, history, min_area, changeThreshold)
    img.compareToReference(ref, threshold)
    print(img.toString())
    periodic_reset = periodic_reset + 1    
    if write_output:
        img.writeImages(args.get("output"))

    r = img.toDict()
    results['files'][img.getShortname()] = r

    if img.getStatus() == DetectMultiFrame.DetectValue.Reset:
        print("Resetting reference")
        ref = None

    # Periodically reset as (probably due to daylight) the image drifts over time.
    # Note: History has to be longer than reset_interval to work
    if periodic_reset > reset_interval and img is not None:
        if img.getStatus() != DetectMultiFrame.DetectValue.Disruption:
            ref = None
            print("Periodic reset")        

    ## TODO improve, allow second and reset of announce
    if not announced and img is not None and len(history) >= announce_threshold:
        # todo update for multi-detection
        if img.getStatus() == DetectMultiFrame.DetectValue.Found and len(img.getAllAreas()) == 1:
            allFound = True
            for dot in history[-announce_threshold:]:
                if dot['Status'] != 'Found':
                    allFound = False
                    break
            if allFound:
                img.writeImages(args.get("output"))
                announce(img)
                announced = True
        
    return img


#### MAIN ###
history = []
max_history = 100

for f in files:

    img = process_image(dir+f, history, pics)
    if (img is not None):
        history.append(img.toDict())

    if len(history) > max_history:
       history.pop(0) 


if not live_mode:
    write_results(results)
    
if live_mode:
    camera = PiCamera()
    camera.start_preview()
    count = 0
    low_res = (320, 240)
    high_res = (640, 480)
    camera.resolution = high_res

    while True:
        for i in range(1,10):
            filename = args.get("output") + 'Incubator_'+ time.strftime('%m%d_%H%M%S')+ '.jpg'
            camera.capture(filename)
            img = process_image(filename, history, pics)
            if (img is not None):
                history.append(img.toDict())
        
            if len(history) > max_history:
               history.pop(0)

            print("Processed ", filename)
            sleep(10)
            sleep(10)
            sleep(10)
            sleep(10)
            sleep(10)
            sleep(9)
            
        write_results(results)
        print('Updated results')

#with open('output/a_results.json') as infile:
#   results = json.load(infile)
print ("Done")      
