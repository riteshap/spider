"""微博热搜"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from SqlServe import SqlServe
from page_analysis.analysis import PageAnalysis
from write_log import WriteLog
from selenium.webdriver.support import expected_conditions as EC
from mainten.phone_connect import phone_login
import os
import cv2
import time
import random
import traceback
import configparser as conf


class WbWebGet:
    def __init__(self, work_dir, driver: webdriver.Chrome, net_mode="01"):
        self.driver = driver
        self.work_dir = work_dir
        self.sqlserver = SqlServe(work_dir=work_dir)
        self.phone = phone_login(self.work_dir)
        self.pas = PageAnalysis()
        self.config_path = os.path.join(work_dir, r"../config/config_main.ini")
        self.config = conf.ConfigParser()
        self.config.read(self.config_path, encoding="utf-8")
        self.net_mode = net_mode  # 01校园网，02互联网
        self.wbr_log = WriteLog(file_name="wbr_log", log_name="wbr", log_level="INFO")
        self.__offline_check(url="https://www.baidu.com")  # 检查网络通畅

    def __get_url(self, aim_url, sleep_time=2):
        try:
            self.driver.get(aim_url)
            time.sleep(sleep_time)
        except Exception as e:
            try:
                self.driver.execute_script("window.stop()")
            except:
                pass

    def __check_quittime(self):
        """检查退出时间为NULL的热搜词条的退出时间，超出72小时则记72小时"""

    def __element_exist(self, xpath):
        try:
            element = WebDriverWait(self.driver, 5, 0.5).until(EC.visibility_of_element_located((By.XPATH, xpath)))
            return True
        except Exception as e:
            return False

    def __offline_check(self, url):
            """
            检测网络状态是否离线，
            mode=01表示校园网环境
            mode=02表示互联网环境
            若已离线则重新连接，若在线则跳转回原链接"""
            net_url = ele_0 = ele_1 = ele_2 = ele_3 = " "
            if self.net_mode == "01":
                net_url = "http://10.0.0.19"
                ele_0 = '//input[@value="注  销"]'
                ele_1 = '//input[@placeholder="账号"]'
                ele_2 = '//input[@placeholder="密码"]'
                ele_3 = '//input[@value="登录"]'
            elif self.net_mode == "02":
                net_url = "https://www.baidu.com"
                ele_0 = '//*[@id="su"]'
            else:
                self.bdr_log.write_in("网络检查模式错误", level="WEEOR")
                raise Exception("网络检查模式错误")

            self.__get_url(net_url)
            flag = self.__element_exist(xpath=ele_0)
            if flag is True:  # 说明在线
                self.__get_url(url)
            elif self.net_mode == "01":  # 校园网离线则断线重连
                flag = self.__element_exist(xpath=ele_1)
                if not flag:
                    self.bdr_log.write_in("网络异常，无法正确登录", level="WEEOR")
                    raise Exception("网络检查模式错误")
                net_account = self.config.get("bdr_main", "net_account")
                passwd = self.config.get("bdr_main", "passwd")
                self.driver.refresh()
                ele = self.driver.find_element(By.XPATH, ele_1)
                ele.send_keys(net_account)
                time.sleep(2)
                ele = self.driver.find_element(By.XPATH, ele_2)
                ele.send_keys(passwd)
                time.sleep(2)
                ele = self.driver.find_element(By.XPATH, ele_3)
                ele.send_keys(Keys.ENTER)
                time.sleep(5)
                self.__get_url(url)
            else:  # 互联网环境无法自动恢复
                self.bdr_log.write_in("网络异常，无法正确登录", level="WEEOR")
                raise Exception("网络异常，无法正确登录")


    def __login(self):
        # 用于处理微博账号登录，当浏览器中微博账号失效需要重新登录时启用
        # 1.检测登录按钮并确保打开登录页面
        save_path = os.path.join(self.work_dir, "QR_code.png")
        cur_handle = self.driver.current_window_handle  # 原微博界面
        for i in range(4):
            self.__get_url("https://weibo.com")
            login_xpath = '//button[contains(@class,"LoginCard")]'  # 微博登录按钮
            if self.__element_exist(login_xpath):
                obj = self.driver.find_element(By.XPATH, login_xpath)
                obj.click()
                time.sleep(6)
            else:
                time.sleep(3)
                continue
            # 2.保证新页面已刷新出二维码，随后将二维码截图推送至手机端
            if len(self.driver.window_handles) != 2:
                raise Exception("浏览器页面异常，出现多个窗口：{}".format(len(self.driver.window_handles)))

            for aa in self.driver.window_handles:  # 切换至二维码界面
                if aa == cur_handle:
                    continue
                self.driver.switch_to.window(aa)

            if self.__element_exist("//img[@class='w-full h-full']"):  # 判断二维码图片是否存在,仍然有可能是白屏
                obj = self.driver.find_element(By.XPATH, '//div[contains(@class,"justify-center w-82.5")]')
                obj.screenshot(save_path)
                break
            else:
                # close新页面并切换回原始页面
                self.driver.close()
                self.driver.switch_to.window(cur_handle)
                continue

        # self.driver.save_screenshot("./QR_code.png")
        QR_code = cv2.imread(save_path)
        save_path2 = os.path.join(self.work_dir, "QR_code.jpg")
        adb_path = os.path.join(self.work_dir, r"mainten\adb")
        cv2.imwrite(save_path2, QR_code)
        os.popen(r"{} push {} /sdcard/DCIM/Camera/".format(adb_path, save_path2))
        time.sleep(4)
        # android的广播机制，需要告知设备图片位置，使得相册能够读取到该图片
        os.popen(r"{} shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE "
                 r"-d file:/sdcard/DCIM/Camera/QR_code.jpg".format(adb_path))

        # 3.启用手机端，用微博app扫描二维码图片完成登录
        self.phone.connect()

        # 4.执行完毕后，若未完成登录，需要关闭所有非主界面的窗口
        for aa in self.driver.window_handles:
            if aa != cur_handle:
                self.driver.switch_to.window(aa)
                self.driver.close()
        self.driver.switch_to.window(cur_handle)

        # 5.最后执行检测，确认是否已完成登录
        login_xpath = '//button[contains(@class,"LoginCard")]'  # 微博登录按钮
        if self.__element_exist(login_xpath):
            self.wbr_log.write_in("微博未完成登录", level="WARNING")


    def __collect_realtime(self, hot_dic):
        


    def weibo_realtime(self):
        last_time = time.time() - 700
        while True:
            if time.time() - last_time < 600:  # 每十分钟采集一次
                time.sleep(60)
                continue
            # 检测网络是否通畅，若出现环境问题则退出循环
            self.__offline_check("https://www.baidu.com/")
            try:
                # 检测是否已登录
                for i in range(4):
                    self.__get_url("https://weibo.com")
                    login_xpath = '//button[contains(@class,"LoginCard")]'  # 微博登录按钮
                    if self.__element_exist('//i[contains(@class,"woo-font--refresh")]'):  # 微博热搜的刷新按钮
                        # 此时说明页面基本已加载
                        if self.__element_exist(login_xpath):
                            self.__login()
                    if self.__element_exist(login_xpath):  # 说明未完成登录
                        if i >= 3:
                            raise Exception("微博登录错误")
                        continue
                    else:
                        break

                # 启动热搜采集
                self.__get_url("https://weibo.com/hot/search")
                # 1.微博热搜会根据页面当前位置调整热搜html内容，因此需要逐步模拟滚轮采集数据
                hot_dic = {}
                for i in range(10):
                    ele_path = "//div[@id='scroller']/div/div[contains(@class,'vue-recycle')]//a"
                    eles = self.driver.find_elements(By.XPATH, ele_path)
                    for ele in eles:
                        title = ele.text
                        href = ele.get_attribute("href")
                        if title not in hot_dic.keys():
                            hot_dic[title] = href
                    # 1.1 向下翻滚一定幅度，继续采集热搜内容
                    # print("滑动一下")
                    js = "window.scrollTo({}, {})".format(i, (i + 1) * 600)
                    self.driver.execute_script(js)  # 模拟鼠标滚轮，滑动页面至底部
                    time.sleep(4)

                # print(hot_dic.keys())



                last_time = time.time()  # 执行采集后更新最后采集时间
            except Exception as e:
                self.wbr_log.write_in(traceback.format_exc(), level="ERROR")