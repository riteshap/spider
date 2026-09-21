from airtest.core.api import *
import cv2 as cv
import time
import os
mode = 0
if mode == 0:
    init_device(platform="Android",uuid="ZLG69HTOQKIRZTRK", cap_method="JAVACAP")
    # connect_device("Android:///")
    #
    dev = device()
    dev.wake()
    time.sleep(5)

    dev.snapshot(filename="test_weibo.png")
pic = cv.imread("test_weibo.png")
x = pic.shape[0]
y = pic.shape[1]
print(x)  # 2400
print(y)  # 1080
ss = pic[1850:2100, 820:950]
cv.imshow("1", ss)
cv.waitKey(0)

cv.imwrite("temp.png", ss)