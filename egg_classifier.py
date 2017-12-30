import EggDetect
import math
import numpy as np
import cv2
import json
import re
import os

# help classifiy potential eggs as egg/not_an_egg to create training data.
class EggClassifier():

    def __init__ (self, output = "classification.json", true_path = "./true/", known_true_locs = [], \
                  pos_true_region = ((0,0), (10000,10000)), false_path = "./false/", \
                  posn_margin = 7, size_margin = 7):
        self.true_path = true_path
        self.false_path = false_path
        self.known_true_locations = known_true_locs
        self.known_false_locations = []
        self.possible_true_region = pos_true_region
        self.size_margin = size_margin
        self.posn_margin = posn_margin
        #set low thresholds
        self.Detector = EggDetect.EggDetect(max_egg_width = 70, min_egg_width = 12 , error_thresh = 150, min_contour_length = 50,
                  edge_high_thresh = 160, edge_low_thresh = 60, ref_width = 4,  ref_blur = 11)

        self.regex = re.compile("(t|T|y|Y)")
        self.regex_skip = re.compile("(s|S)")
        self.output = []

    # compute difference in posn and size b/w 2 ellipses
    def diff(self, e1, e2):
        posn = math.sqrt((e1[0][0] - e2[0][0])**2 + (e1[0][1] - e2[0][1])**2)
        #biggest difference between each axes
        h = abs(np.max(e1[1]) - np.max(e2[1]))
        w = abs(np.min(e1[1]) - np.min(e2[1]))
        #print("diff p/h/w :", posn, h, w)

        return (posn, h, w)

    def isKnown(self, ellipse):
        found = False
        for p in self.known_true_locations:
            print("P", p)
            diff = self.diff(ellipse, p)
            if diff[0] < self.posn_margin and diff[1] < self.size_margin and diff[2] < self.size_margin:
                print("Close enough")
                found = True
            #else:
                #print("Not close enough")
        return found

    def isKnownBad(self, ellipse):
        found = False
        for p in self.known_false_locations:
            # print("P", p)
            diff = self.diff(ellipse, p)
            if diff[0] < self.posn_margin and diff[1] < self.size_margin and diff[2] < self.size_margin:
                #print("Close enough")
                found = True
            #else:
                #print("Not close enough")
        return found

    def isPossible(self, ellipse):
        x = ellipse[0][0]
        y = ellipse[0][1]

        OK = False
        #print(ellipse[0][0], ellipse[0][1])
        if self.possible_true_region[0][0] <= x <= self.possible_true_region[1][0] and \
           self.possible_true_region[0][1] <= y <= self.possible_true_region[1][1]:
            OK = True
            print("Inside")
        else:
            print("Outside")

        return OK

    def get_crop(self, img, ellipse, filename = ""):
        center = ellipse[0]
        length = max(ellipse[1])

 #       print("C", center, length)

        x1 = int(center[1] - length)
        y1 = int(center[0] - length)
        x2 = int(center[1] + length)
        y2 = int(center[0] + length)

        rows, cols = img.shape

        if x1 < 0 or x2 > cols or y1 < 0 or y2 > rows:
            print("too close to edge")
            return 0


        crop = img[x1:x2, y1:y2]
 #       print("X", y1, y2)
        cv2.imshow("crop", crop)
        if len(filename) > 0:
 #           print("Write : ", filename)
            cv2.imwrite(filename, crop)
        return crop

    def process_true(self, egg):
 #       imgc = np.copy(self.img)
 #       imgc = cv2.ellipse(imgc, egg["ellipse"], (255,255,255), 2)
 #       cv2.imshow("True", imgc)
        file, ext = os.path.splitext(egg["file"])
        crop_fn = self.true_path + "/" + file + "_" + str(egg["cnt"])
        self.get_crop(self.img, egg["ellipse"], crop_fn + ext)
        self.get_crop(self.edges, egg["ellipse"], crop_fn + "e" + ext)

        egg["crop"] = crop_fn + ext
        egg["classification"] = "EGG"

        self.cimg = cv2.ellipse(self.cimg, egg["ellipse"], (0, 255, 0), 2)
        return egg

    def process_false(self, egg):
#        imgc = np.copy(self.img)
 #       imgc = cv2.ellipse(imgc, egg["ellipse"], (255,255,255), 2)
 #       cv2.imshow("False", imgc)
        file, ext = os.path.splitext(egg["file"])
        crop_fn = self.false_path + "/" + file + "_" + str(egg["cnt"])
        self.get_crop(self.img, egg["ellipse"], crop_fn + ext)
        self.get_crop(self.edges, egg["ellipse"], crop_fn + "e" + ext)

        egg["crop"] = crop_fn + ext
        egg["classification"] = "FALSE"
        self.cimg = cv2.ellipse(self.cimg, egg["ellipse"], (0, 0, 255), 2)

        return egg

    def classify(self, filename):

        self.img = self.Detector.load(filename)
        self.edges = self.Detector.find_edges(self.img)
        self.cimg = cv2.imread(filename, 1)

        eggs = self.Detector.find_eggs(filename)
        cnt = 0


 #       path, file = os.path.split(filename)
 #       file, ext = os.path.splitext(file)

        for egg in eggs:
            imgc = np.copy(self.img)
            imgc = cv2.ellipse(imgc, egg["ellipse"], (255,255,255), 1)
            cv2.imshow("CHECK", imgc)
            egg["cnt"] = cnt
            cnt = cnt+1
            #print("FOUND : ", egg)
            if self.isKnown(egg["ellipse"]):
                print("is known")
                self.output.append(self.process_true(egg))
                #input("Known")
            elif self.isKnownBad(egg["ellipse"]):
                print("is known Bad")
                self.output.append(self.process_false(egg))
                #input("Known")
            elif self.isPossible(egg["ellipse"]):
 #               cimg = cv2.ellipse(cimg, egg["ellipse"], (255, 0, 0), 2)
                print("is possible : ", egg["ellipse"])
                answer = ""
                while len(answer) < 1:
                    answer = input("Check y/n: ")
                    if self.regex.search(answer):
                        print("YES")
                        self.output.append(self.process_true(egg))
                        if not self.regex_skip.search(answer):
                            self.known_true_locations.append(egg["ellipse"])
                            print ("Known Good Locations: ", len(self.known_true_locations))
                        else:
                            print("ANS", answer)
 #                       cimg = cv2.ellipse(cimg, egg["ellipse"], (0, 255, 0), 2)
                    elif len(answer) > 0:
                        print("NO")
                        self.output.append(self.process_false(egg))
                        if not self.regex_skip.search(answer):
                            self.known_false_locations.append(egg["ellipse"])
                            print ("Known Bad Locations: ", len(self.known_false_locations))
#                       cimg = cv2.ellipse(cimg, egg["ellipse"], (0, 0, 255), 2)

            else:
                print("not possible")
                self.output.append(self.process_false(egg))
                #input("Nope")
 #               cimg = cv2.ellipse(cimg, egg["ellipse"], (0, 0, 255), 2)

        if self.cimg is not None:
            f = open("res.json", 'w')
            #print(output)
            json.dump(self.output, f)
            f.close()
            cv2.imshow("Result", self.cimg)
