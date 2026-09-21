from airtest.core.api import *
from poco.drivers.android.uiautomation import AndroidUiautomationPoco
import configparser as conf
import cv2 as cv
import time
import os

class phone_login:
    def __init__(self, work_dir):
        self.work_dir = work_dir
        self.config = conf.ConfigParser()
        self.config_path = os.path.join(self.work_dir, r"./config/config_order.ini")
        self.config.read(self.config_path, encoding="utf-8")
        self.uuid = self.config.get("ord_main_win", "uuid")
        print(self.uuid)
        init_device(platform="Android", uuid=self.uuid, cap_method="JAVACAP")
        self.poco = AndroidUiautomationPoco()
        # connect_device("Android:///")
        self.dev = device()

    def match_temp(self, temp_file_name, min_val_limit, shift_x, shift_y):
        self.dev.snapshot(filename="test_weibo.png")
        time.sleep(2)
        pic = cv.imread("test_weibo.png")
        temp_path = os.path.join(self.work_dir, "mainten/{}".format(temp_file_name))
        pic_obj = cv.imread(temp_path)  # 读取模板图片
        result = cv.matchTemplate(pic, pic_obj, method=0, result=None, mask=None)  # 比对
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result)  # 确定模板图片位置
        print(min_val)
        if min_val < min_val_limit:
            return (min_loc[0] + shift_x, min_loc[1] + shift_y)
        else:
            return "未识别到物块"

    def obj_click(self, name, obj_name):
        for i in range(4):
            if self.poco(name=name).exists():
                self.poco(name=name).click()  # 点击相册按钮
                time.sleep(2)
                break
            else:
                time.sleep(2)
            if i >= 3:
                raise Exception("{}点击超时".format(obj_name))

    def connect(self):
        # ans = os.popen(r"E:\python_code\spider\mainten\adb devices")
        # time.sleep(6)

        self.dev.wake()  # 唤醒设备，不能有锁屏
        time.sleep(4)
        self.dev.start_app("com.sina.weibo")
        time.sleep(8)
        # 在微博中点击“我的”
        ret_ans = self.match_temp(temp_file_name="temp_me.png",
                                   min_val_limit=2e6,
                                   shift_x=40,
                                   shift_y=40)
        if type(ret_ans) != str:
            self.dev.touch((ret_ans[0], ret_ans[1]))
            time.sleep(2)
        else:
            self.dev.snapshot("error.jpg")
            raise Exception(ret_ans)
        # 在微博中点击“扫描”按钮
        ret_ans = self.match_temp(temp_file_name="temp_scan.png",
                                   min_val_limit=2e6,
                                   shift_x=40,
                                   shift_y=40)
        if type(ret_ans) != str:
            self.dev.touch((ret_ans[0], ret_ans[1]))
            time.sleep(2)
        else:
            self.dev.snapshot("error.jpg")
            raise Exception(ret_ans)

        self.obj_click("com.sina.weibo:id/scan_my_photo_icon", "相册")

        # for i in poco(name="com.sina.weibo:id/thumbnail"):  # 遍历相册内图片文件
        #     print(i.attr("pos"))
        # time.sleep(2)
        for i in range(3):
            if self.poco(name="com.sina.weibo:id/thumbnail").exists():
                break
            else:
                time.sleep(2)
        self.poco(name="com.sina.weibo:id/thumbnail")[0].click()  # 说明同名元素是可以查找为列表的
        time.sleep(2)
        self.poco(name="android.widget.TextView", text="允许登录").click()
        time.sleep(5)
        # print("over")
        self.dev.stop_app("com.sina.weibo")


