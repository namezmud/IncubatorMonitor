import json
import imutils
import time
import cv2
import os
import re
import incimagedetect
import incnotify
import picamera
from enum import Enum
from picamera import PiCamera
from time import sleep

class IncDetection():

    def __init__ (self, files = [], output_path = '/tmp/', min_area = 2500, threshold = 25, reset_threshold = 50000,
                  reset_interval = 60, notify_level = 1, notify_on = False,
                  notify_threshold = 3, write_images = True):
        self.files = files
        self.min_area = min_area
        self.threshold = threshold
        self.reset_threshold = reset_threshold
        self.reset_interval = reset_interval
        self.notify_level = notify_level
        self.notify_threshold = notify_threshold
        self.notify = None
        self.notification_sent = False
        self.reset_counter = 0
        self.history = []
        self.output_path = output_path
        self.max_history = max(100, reset_threshold)
        self.write_images = write_images
        
        self.ref = None

        # Store some basic info in the output so we can track them against results
        results = {}
        results['files'] = {}
        results['settings'] = {}
        results['settings']['threshold'] = threshold
        results['settings']['min_size'] = min_area
        results['settings']['change_threshold'] = reset_threshold
        results['settings']['files'] = len(files)
        self.results = results


        # setup notification is enabled
        if notify_on:
            self.notify = incnotify.IncNotify()
            
    def write_results(self):
        # Don't stop if results can't be written.  Non-critical
        try:
            file = self.output_path +'/a_results.json'
            with open(file, 'w') as outfile:
                json.dump(self.results, outfile)
        except:
            print("Unable to write results to", file)
        
    
    def process_image(self, f):

        img = None
        
        # if no reference set, (or it is being reset), create a reference with this image.
        if self.ref is None:
            self.ref = incimagedetect.DetectFrame(f)
            print("New reference ", self.ref.getShortname())
            self.reset_counter = 0
        else:

            img = incimagedetect.DetectFrame(f, self.history, self.min_area, self.reset_threshold)
            img.compareToReference(self.ref, self.threshold)
            print(img.toString())
            self.reset_counter = self.reset_counter + 1
            
            if self.write_images:
                # don't fail if we can't write output. we'll get over it (or recreate them in replay)
                try:
                    img.writeImages(self.output_path)
                except BaseException as e:
                    print("Failed to write output images", type(e).__name__)

                r = img.toDict()
                self.results['files'][img.getShortname()] = r

            # Clear the reference image if the motion detections says we need to.
            if img.getStatus() == incimagedetect.DetectValue.Reset:
                print("Resetting reference")
                self.ref = None

            # Periodically reset as (probably due to daylight) the image drifts over time.
            # Note: History has to be longer than reset_interval to work
            if self.reset_counter > self.reset_interval and img is not None:
                if img.getStatus() != incimagedetect.DetectValue.Disruption:
                    self.ref = None
                    print("Periodic reset")        

            # Detect new hatching and send notification if enabled.
            ## TODO improve, allow second and reset of notification
            if (self.notify is not None and not self.notification_sent and
                    img is not None and len(self.history) >= self.notify_threshold):
                # todo update for multi-detection
                if img.getStatus() == incimagedetect.DetectValue.Found and len(img.getAllAreas()) == 1:
                    allFound = True
                    for dot in self.history[-self.notify_threshold:]:
                        if dot['Status'] != 'Found':
                            allFound = False
                            break
                    if allFound:
                        img.writeImages(self.output_path)
                        self.notify.notify(img, self.notify_level)
                        self.notification_sent = True

            if img is not None:
                self.history.append(img.toDict())

                # todo use deque
                if len(self.history) > self.max_history:
                    self.history.pop(0)
                
        return img

    def go(self):
        if len(self.files) > 0:
            self.go_replay()
        else:
            self.go_live()

    def go_replay(self):
        
        for f in self.files:
            img = self.process_image(f)

        self.write_results()   

    def go_live(self):
    
        camera = PiCamera()
        camera.start_preview()
        high_res = (640, 480)
        camera.resolution = high_res

        while True:
            for i in range(1,10):
                filename = self.output + 'Incubator_'+ time.strftime('%m%d_%H%M%S')+ '.jpg'
                camera.capture(filename)
                img = self.process_image(filename)

                print("Processed ", filename)

                #todo configure interval
                #split sleep to allow quicker interruption
                sleep(10)
                sleep(10)
                sleep(10)
                sleep(10)
                sleep(10)
                sleep(9)

            #write results periodically as it will probably end in tears (i.e. ctrl-C)
            write_results(results)
            print('Updated results')
