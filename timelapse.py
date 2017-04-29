#!/home/pi/.virtualenvs/cv/bin/python3
import cv2
import os

class TimeLapse():

        def __init__(self, rate = 5, codec = 'FMP4', ext = 'avi'):
                self.rate = rate
                self.codec = codec
                self.ext = ext
                

        def build_video(self, files, output_file):

                video = None
                frames = 0
                for f in files:
                        if f.endswith(".jpg") and os.path.isfile(f):
                                im = cv2.imread(f)
                                if video is None and im is not None:
                                        video = cv2.VideoWriter(output_file + "." + self.ext, cv2.VideoWriter_fourcc(*self.codec), 5, (len(im[0]), len(im)))

                                if im is not None:
#                        print(len(im), len(im[0]))
                                        frames = frames + 1
                                        video.write(im)
  
                if video is not None:
                        video.release()
                return frames

        def getCodec(self):
                return self.codec

        def getRate(self):
                return self.rate
                
###define codec
##files = os.listdir("output")
##
##for f in files:
##        if f.endswith(".jpg"):
###                print(f)
##                im = cv2.imread("output/"+f)
##                if not isOpen:
##                        out = cv2.VideoWriter("testfmp4_5.avi", cv2.VideoWriter_fourcc(*'FMP4'), 5, (len(im[0]), len(im)))
##                        isOpen = True
##
##                if im is not None:
###                        print(len(im), len(im[0]))
##                        out.write(im)
##
##out.release()

def __main__():
        t = TimeLapse(rate = 5)
        files = os.listdir("output")
        t.build_video(files, "/tmp/video")
        
