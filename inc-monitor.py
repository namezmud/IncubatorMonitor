#!/home/pi/.virtualenvs/cv/bin/python3
import argparse
import time
import numpy
import os
import incdetect

# arg parser
ap = argparse.ArgumentParser()
ap.add_argument("-d", "--dir", default="ref/", help="Directory containing image files")
ap.add_argument("-a", "--min_area", type=int, default=2500, help="Minimum size in pixels of a motion area.")
ap.add_argument("-t", "--thresh", type=int, default=30, help="Intensity difference threshold.")
ap.add_argument("-o", "--output", default="output/", help="Output directory")
ap.add_argument("-c", "--change", type=int, default=50000, help="Pixel Change to set new reference")
ap.add_argument("-n", "--tweet", nargs='?', const='Y', default='N', help="enable twitter")
ap.add_argument("-l", "--live", nargs='?', const='Y', default='N', help="Use live Cam")

args = vars(ap.parse_args())

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

reset_interval = 60
notify_threshold = 3
notify_level = 1

pics = True
results = {}
results['files'] = {}

if live_mode:
    paths = []
else:
    files = os.listdir(dir)
    files.sort()
    print(len(files), "files found")
    
    paths = [dir + f for f in files]

    
inc = incdetect.IncDetection(files = paths, output_path = args.get("output"),
                             min_area = args.get("min_area"),
                             threshold = args.get("thresh"), reset_threshold=args.get("change"),
                             reset_interval = reset_interval, notify_threshold = notify_threshold,
                             notify_on = args.get("tweet") == 'Y', notify_level = notify_level)

inc.go()

#with open('output/a_results.json') as infile:
#   results = json.load(infile)
print ("Done")      
