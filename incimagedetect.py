#!/home/pi/.virtualenvs/cv/bin/python3
import datetime
import time
import cv2
import os
import re
import imutils
from enum import Enum

# define alert states
class DetectValue(Enum):
    Empty = 0
    Found = 1
    Reset = 2
    Disruption = 3
    Unknown = 4

def clip(val, min_, max_):
    return min_ if val < min_ else max_ if val > max_ else val

class DetectFrame:

   se = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
   stable_after_reset = 2
   disruption_threshold = 2
   reset_interval = 10
   max_disrupt = 3
   box_display_pad = 10

   def __init__(self, path, history=[], min_size=2500, changeThreshold=50000):
      self.path = path
      self.areas = []
      self.raw = None
      self.processed = []
      self.delta = []
      self.thresh = []
      self.dilate = []
      self.contours = []
      self.output = []
      self.output_path = None
      self.min_size = min_size
      self.changeThreshold = changeThreshold
      self.history = history
      self.ref = None

      if not os.path.isfile(self.path):
          print("No file ", self.path)
          
      assert(os.path.isfile(self.path))
    
      r = cv2.imread(self.path)
      self.raw = imutils.resize(r, width=500)
      blur = cv2.GaussianBlur(self.raw, (9,9), 0)
      self.processed = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)

   def getShortname(self):
      ma = re.search(r'(.*)\.jpg$', os.path.basename(self.path))
      assert (ma != None)
      short = ma.group(1)
      return short

   def getRefname(self):
      if (self.ref != None):
         return self.ref.getShortname()
      else:
         return "None"

   def isOpen(self):
      return len(self.processed) > 0

   def compareToReference(self, ref_obj, threshold):
      # todo check obj type ref_obj
      assert(len(self.processed) == len(ref_obj.processed))
      # todo use method
      self.delta = cv2.absdiff(self.processed, ref_obj.processed)
      self.thresh = cv2.threshold(self.delta, threshold, 255, cv2.THRESH_BINARY)[1]
      self.dilate = cv2.dilate(self.thresh, self.se, iterations=4)
      (_, self.contours, _) = cv2.findContours(self.dilate.copy(), cv2.RETR_EXTERNAL,
                           cv2.CHAIN_APPROX_SIMPLE)
      self.output = self.raw
      
      for c in self.contours:
         self.areas.append(cv2.contourArea(c))
         (x, y, w, h) = cv2.boundingRect(c)

         x = clip(x - self.box_display_pad, 0, 499)
         y = clip(y - self.box_display_pad, 0, 499)
         w = clip(w + 2*self.box_display_pad, 0, 499)
         h = clip(h + 2*self.box_display_pad, 0, 499)
         
         _ = cv2.rectangle(self.output, (x,y), (x+w, y+h), (0,200,0), 2)

      self.ref = ref_obj

   def getTotalDelta(self):
      return sum(self.areas)

   def getAllAreas(self):
      return self.areas

   def getDetectionAreas(self):
      da = []
      for a in self.areas:
         if a > self.min_size:
               da.append(a)
      return da

   def isReset(self):
       reset = sum(self.areas) > self.changeThreshold

       stable = 0

       if len(self.history) > 0 and self.history[-1]['Status'] == 'Reset':
           for i in reversed(self.history):
               if i['Status'] == 'Reset' and sum(i['Areas']) == 0:
                   stable = stable + 1
               else:
                   break           

           if self.history[-1]['Status'] == 'Reset' and stable < self.stable_after_reset:
               reset = True

       # Reset if extended disruption occurs
       if not reset and self.isDisruption() and len(self.history) >= self.max_disrupt:
           disrupt = True
           for dot in self.history[-self.max_disrupt:]:
               if dot['Status'] != DetectValue.Disruption:
                   disrupt = False
                   break
           if disrupt:
              reset = True
              # todo add ut
              print("Extended disruption")

       # Stabilise after reset, reset if there is this is the first update and there is still some change.      
       if len(self.history) == 0 and sum(self.areas) > 0:
            reset = True

       return reset
    
   def isDisruption(self):
       
       disrupt = len(self.history) > 0 and len(self.getAllAreas()) >= len(self.history[-1]['Areas']) + self.disruption_threshold

       return disrupt

   def isEmpty(self):
       empty = not self.isReset() and len(self.getDetectionAreas()) == 0
       return empty

   def isFound(self):
       found = not self.isReset() and not self.isDisruption()
       return found
    
   def getStatus(self):
      s = DetectValue.Unknown

      if self.isReset():
         s = DetectValue.Reset
      elif self.isDisruption():
         s = DetectValue.Disruption
      elif self.isEmpty():
         s = DetectValue.Empty
      elif self.isFound():
         s = DetectValue.Found
      else:
         s = DetectValue.Unknown
      return s

   def getContours(self):
      return self.contours

   def writeImages(self, path):
       dirname = os.path.dirname(path)
       cv2.imwrite(dirname+'/'+self.getShortname()+'_dilate.jpg', self.dilate)
       cv2.imwrite(dirname+'/'+self.getShortname()+'_thresh.jpg', self.thresh)
       cv2.imwrite(dirname+'/'+self.getShortname()+'_delta.jpg', self.delta)

         
       self.output_path = dirname+'/'+self.getShortname()+'_box.jpg'
       cv2.imwrite(self.output_path, self.output)

   def toString(self):
      s = self.getShortname() + " Areas " + str(self.getAllAreas()) + " Total " + str(self.getTotalDelta()) + "/" + str(len(self.getDetectionAreas())) + " Status " + str(self.getStatus()) + " Ref " + self.getRefname()
      return s

   def toDict(self):
      d = {}
      d['Areas'] = self.getAllAreas()
      d['Status'] = self.getStatus().name
#      d['Contours'] = self.getContours()
      d['Reference'] = self.getRefname()

      return d

