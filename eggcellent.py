import cv2
import numpy as np
import matplotlib.pyplot as plt
import math
import os
import egg_svm
import imutils

## Train a Machine Learning system to detect eggs from an image.
class EggDetect():

    # Egg dimensions, contour lengths are in pixels
    # edge thresholds are in intensities based on 8bit images
    def __init__ (self, max_egg_width=60, min_egg_width=15 , error_thresh=120,
                  min_contour_length=70, edge_high_thresh=180,
                  edge_low_thresh=100, ref_width=4, ref_blur=11,
                  break_contours=True):
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
        self.debug = 0
        self.rows = 0
        self.cols = 0
        self.error_thresh = error_thresh
        # currently use an SVM for the ML.
        self.svm = egg_svm.ML()
        self.trained = False
        self.break_contours = break_contours
        self.break_min_length = 160
        self.break_step_size = 50
        self.break_length = 120

    # Train the SVM with known True/False dataset.
    # raw is a list of dicts:
    #   {'ellipse': [[198.57333374023438, 432.1234130859375],  ( A cv2 rouned rectangle)
    #   [12.666114807128906, 22.406574249267578], 121.10914611816406],
    #   'error': 53.15189873417721}
    #
    def train(self, raw):
        self.svm.setData(raw)
        self.svm.run_test()
        self.trained = True

    # TODO Load a trained svm.

    # For a given file find eggs in the image using the trained ML algorithm
    def find_eggs(self, filename):
        self.img = self._load(filename)
        self.pos = self._find_potential_eggs()
        self.pred = self.svm.predict(self.pos)
        cimg = cv2.imread(filename, 1)
        for i in range(len(self.pos)):
            if self.pred[i]:
                col = (0,255,0)
            else:
                col = (0,0,255)

            self.draw(cimg, self.pos[i]["ellipse"], np.array(self.pos[i]["contour"]), col)

    # add the ellipse and contour to the markup image for diagnostics.
    # Note: it updates in place the passed in image so you can accumulate markups.
    #
    def draw(self, img, ellipse, contour, color = (0, 255, 255)):
        markup = img;
        markup = cv2.ellipse(markup, ellipse, color, 2)
        markup = cv2.drawContours(markup, contour, -1, (255, 0, 0), 2)
        cv2.imshow("Markup", markup)
        cv2.imwrite("markup.jpg", markup)
        return markup
        #input("press")

    # load a file to detect eggs in.
    def _load(self, filename):
        self.img = cv2.imread(filename, 0)
        path, self.filename = os.path.split(filename)

        if self.img is None:
            print("failed to _load : ", filename)
            return

        if (self.debug):
            cv2.imshow("Image", self.img)

        self.rows, self.cols = self.img.shape

        return self.img

    # find the edges in a _loaded 8bit image.
    #
    def _find_edges (self):

        self.edges = cv2.Canny(self.img, self.edge_low_thresh, self.edge_high_thresh, 5)
        if self.debug:
            cv2.imshow("Edges", self.edges)
            cv2.imwrite("edges.jpg", self.edges)

        return self.edges

    # from the edges find contours
    def _find_contours (self, edges):
        im, self.contours, heir = cv2.findContours(edges,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)

        return self.contours

    # Compute an error function to measure the error from the controur to the fitted ellipse:
    # return the average error between the contour and to ellipse fitted to it.
    #
    def _get_error(self, contour, ellipse):
        # create an image based on the ellipse fitted where the intensities represent the magnitude
        # of error for each point in the contour compared to the ellipse that is fit.
        # basically does the contour look like the ellipse?

        # build an image where the error increases the further from the fit ellipse.
        err_image = cv2.ellipse(255*np.ones((self.rows, self.cols), np.uint8), ellipse, (0, 0, 0), self.ref_width)
        err_image = cv2.GaussianBlur(err_image, (self.ref_blur, self.ref_blur), 0)

        err = []
        # check all points in the contour against the reference image.
        for p in contour:
           #print(p[0][1], p[0][0], len(p))
           err.append(err_image[p[0][1], p[0][0]])

        # take the mean of the error.  Should this be the square of the error?
        mean_err = np.mean(err) - np.min(err_image)
        return mean_err

    def _get_crop(self, img, ellipse, pad=0):
        pimg = cv2.copyMakeBorder(img, pad, pad, pad, pad, cv2.BORDER_REPLICATE)

        length = max(ellipse[1])
        center = ellipse[0]
        x1 = int(center[1] - length + pad)
        y1 = int(center[0] - length + pad)
        x2 = int(center[1] + length + pad)
        y2 = int(center[0] + length + pad)

        rows, cols = pimg.shape

        if x1 < 0 or x2 > cols or y1 < 0 or y2 > rows:
            print("too close to edge", x1, y1, x2, y2)
            return []

        crop = pimg[x1:x2, y1:y2]
 #       print("X", y1, y2)
        cv2.imshow("padded", crop)
        return crop

    def _compute_medians(self, ellipse):
        pad = 1000
        ff = np.array([range(3), range(3,6), range(6,9)], np.uint8)
        crop = self._get_crop(self.img, ellipse, pad)
        file = ""

        if not len(crop):
            print("failed to get crop")
            return 0*range(10)

        feature_map = imutils.resize(ff, width=max(crop.shape))

        crop_ellipse = ((len(crop)/2, len(crop)/2),
              (ellipse[1][0], ellipse[1][1]),
              ellipse[2])
        cv2.ellipse(feature_map, crop_ellipse, (9,9,9),-1)
        features = [ [] for _ in range(10)]
        for x in range(crop.shape[0]):
            for y in range(crop.shape[1]):
                f = feature_map[x][y]
                v = crop[x][y]
                features[f].append(v)

        medians = [np.median(f) for f in features]

        #repalce any missing data with a middle value
        medians = [127 if not np.isfinite(x) else x for x in medians]

        return medians

    # Check for 1 contour if it could be an egg or not based simple criteria.
    # this is basic filtering of this that are clearly not eggs.
    #
    def _check_contour(self, img, c):

        # Use on contours than are long enough
        # print("Length : ", len(c))
        found = False
        if len(c) > self.min_contour_length:
            m = img
            m = cv2.drawContours(m, c, -1, (255, 0, 0), 2)
            if self.debug:
                cv2.imshow("contour", m)
                cv2.imwrite("contour.jpg", m)

            # fit an ellipse to the contour (cos eggs are egg shaped)
            print("Length : ", len(c))
            fit_ellipse = cv2.fitEllipse(c)
            ellipse_dims = fit_ellipse[1]
            print("Ellipse dimensions : ", fit_ellipse)

            #check if the ellipse is in the range to be an egg
            #self.draw(img, fit_ellipse, c)
            if self.min_width <= ellipse_dims[0] <= self.max_width and \
                    self.min_width <= ellipse_dims[1] <= self.max_width:

                # compute an error based on the contour vs. the ellipse.
                error = self._get_error(c, fit_ellipse)

                print ("Error = ", error)

                # Discard if greater than a coarse filter on error.
                if error < self.error_thresh:
                    print("Error OK", fit_ellipse)
                    too_close = False

                    for egg in self.eggs:

                       dist = math.sqrt((egg["ellipse"][0][0] - fit_ellipse[0][0])**2 +
                                        (egg["ellipse"][0][1] - fit_ellipse[0][1])**2)

                       # disabled too close check for now.
                       #if dist < self.min_width:
#                             too_close = True
#                              print("Too close to another egg")

                    # just take the first one at this stage. TODO: take the best one
                    if not too_close:
                        self.draw(img, fit_ellipse, c)
                        print("Found egg : ", fit_ellipse)
                        meds = self._compute_medians(fit_ellipse)
                        egg_out = {"ellipse": fit_ellipse, "error" : error, "contour" :
                                   c.tolist(), "file":self.filename,
                                   "median_ints":meds}
                        self.eggs.append(egg_out)
                        found = True
                        #input("press")
        return found

    # detect all eggs from a list of contours.
    #
    def _get_eggs_from_contours(self, contours):
        img = np.copy(self.img)
        self.eggs = []
        for c in contours:
            found = self._check_contour(img, c)

            # if enabled, break long contours in to smaller ones to find eggs
            # adjacent to other detected edges
            if self.break_contours and len(c) > self.break_min_length:
                slice_start = 0
                slice_end = self.break_length
                # test slices as contours.
                while slice_end < len(c):
                    self._check_contour(img, c[slice_start:slice_end])
                    slice_start += self.break_step_size
                    slice_end += self.break_step_size

        return self.eggs

    # find potential matches in the _loaded image.
    # looks for edges that meet the basic criteria.
    #
    def _find_potential_eggs(self):
        eggs = []

        if self.img is not None:

            edges = self._find_edges()
            # convert to list to ease serialization for json.
            contours = self._find_contours(edges)
            print("arr type", type(contours))
            eggs = self._get_eggs_from_contours(contours)
        return eggs
