import cv2
import numpy as np
import matplotlib.pyplot as plt
import math

class EggDetect():

    def __init__ (self, max_egg_width = 60, min_egg_width = 15 , error_thresh = 60, min_contour_length = 70,
                  edge_high_thresh = 180, edge_low_thresh = 80, ref_width = 4,  ref_blur = 11):
        self.max_width = max_egg_width
        self.min_width = min_egg_width
        self.ref_width = ref_width
        self.ref_blur = ref_blur
        self.min_contour_length = min_contour_length
        self.edge_high_thresh = edge_high_thresh
        self.edge_low_thresh = edge_low_thresh
        self.img = []
        self.edges = 0
        self.contours = []
        self.debug = 1
        self. rows = 0
        self.cols = 0
        self.error_thresh = error_thresh

    def find_edges (self, img):
        self.edges = cv2.Canny(img, self.edge_low_thresh, self.edge_high_thresh)
        if self.debug:
            cv2.imshow("Edges", self.edges)
        
        return self.edges

    def find_contours (self, edges):
        im, self.contours, heir = cv2.findContours(edges,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)
        
        return self.contours

    #return the average error between the contour and to ellipse fitted to it.
    def get_error(self, contour, ellipse):                                              
        # create an image based on the ellipse fitted where the intensities represent the magnitude
        # of error for each point in the contour compared to the ellipse that is fit.
        # basically does the contour look like the ellipse?
 #       ref_width = int(np.max(ellipse[1]) * 0.1)
 #       print("ref_width ", ref_width)
        err_image = cv2.ellipse(255*np.ones((self.rows, self.cols), np.uint8), ellipse, (0, 0, 0), self.ref_width)
        err_image = cv2.GaussianBlur(err_image, (self.ref_blur, self.ref_blur), 0)

        err = []                                       
        for p in contour:      
           #print(p[0][1], p[0][0], len(p))
           err.append(err_image[p[0][1], p[0][0]])

        mean_err = np.mean(err) - np.min(err_image)
        return mean_err

    def draw(self, img, ellipse, contour):
        markup = img;
        markup = cv2.ellipse(markup, ellipse, (0,255,0), 2)
        markup = cv2.drawContours(markup, contour, -1, (255, 0, 0), 2)
        cv2.imshow("Markup", markup)
        #input("press")
        
    def get_eggs_from_contours(self, _img, contours):
        img = np.copy(_img)
        self.eggs = []
        for c in contours:
            # Use on contours than are long enough
            # print("Length : ", len(c))
            if len(c) > self.min_contour_length:
                # fit an ellipse to the contour (cos eggs are egg shaped)
                print("Length : ", len(c))
                fit_ellipse = cv2.fitEllipse(c)
                ellipse_dims = fit_ellipse[1]
                print("Ellipse dims : ", ellipse_dims)
                #check if the ellipse is in the range to be an egg
                #self.draw(img, fit_ellipse, c)
                if self.min_width <= ellipse_dims[0] <= self.max_width and \
                self.min_width <= ellipse_dims[1] <= self.max_width:
                    error = self.get_error(c, fit_ellipse)

                    print ("Error = ", error)

                    if error < self.error_thresh:
                        print("Error OK", fit_ellipse)
                        too_close = False
                        for egg in self.eggs:
                           dist = math.sqrt((egg[0][0] - fit_ellipse[0][0])**2 + (egg[0][1] - fit_ellipse[0][1])**2)
                           if dist < self.min_width:
                               too_close = True
                               print("Too close to another egg")

                        # just take the first one at this stage. TODO: take the best one      
                        if not too_close:
                            self.draw(img, fit_ellipse, c)
                            print("Found egg : ", fit_ellipse)
                            self.eggs.append(fit_ellipse)
                            input("press")
                #input("press")
        return self.eggs

    def load(self, filename):
        self.img = cv2.imread(filename, 0)

        if self.img is None:
            print("failed to load : ", filename)
            return

        if (self.debug): 
            cv2.imshow("Image", self.img)

        self.rows, self.cols = self.img.shape
         
        return self.img

                    
    def find_eggs(self, filename):
        eggs = []
        img = self.load(filename)

        if img is not None:

            edges = self.find_edges(img)
            contours = self.find_contours(edges)
            eggs = self.get_eggs_from_contours(img, contours)
        return eggs
