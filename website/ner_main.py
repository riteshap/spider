"""网易热搜"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from SqlServe import SqlServe
from page_analysis.analysis import PageAnalysis
from write_log import WriteLog
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import random
import pickle
import traceback
import configparser as conf


class NeWebGet:
    def __init__(self, work_dir, driver: webdriver.Chrome, net_mode="01"):
        self.driver = driver
        self.work_dir = work_dir
        self.pid = os.getpid()
        pickle.dump(self.pid, open("002_pid", "wb"))
        self.sqlserver = SqlServe(work_dir=self.work_dir)
        self.pas = PageAnalysis()
        self.config_path = os.path.join(self.work_dir, r"../config/config_main.ini")
        self.config = conf.ConfigParser()
        self.config.read(self.config_path, encoding="utf-8")
        self.net_mode = net_mode  # 01校园网，02互联网
        self.ner_log = WriteLog(file_name="ner_log", log_name="ner", log_level="INFO")
        self.realtime_hour = int(time.strftime("%H", time.localtime()))  # 用于控制重置热搜id号码
        self.realtime_id_num = 0  # 用于累计计算id号码
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

    def __element_exist(self, xpath, ele=None, timeout=5):
        try:
            if ele is None:
                element = WebDriverWait(self.driver, timeout=timeout, poll_frequency=0.5).until(EC.visibility_of_element_located((By.XPATH, xpath)))
                return True
            else:
                element = ele.find_element(By.XPATH, xpath)
                element.is_enabled()
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
            self.ner_log.write_in("网络检查模式错误", level="WEEOR")
            self.driver.quit()
            raise Exception("网络检查模式错误")

        for i in range(3):
            self.__get_url(net_url)
            flag = self.__element_exist(xpath=ele_0)
            if flag is True:  # 说明在线
                # self.__get_url(url)
                return True
            elif self.net_mode == "01":  # 校园网离线则断线重连
                flag = self.__element_exist(xpath=ele_1)
                if not flag:
                    self.ner_log.write_in("网络异常，无法正确登录", level="WEEOR")
                    return False
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
                return True
            elif i < 2:
                continue
            else:  # 互联网环境无法自动恢复
                self.ner_log.write_in("网络异常，无法正确登录", level="WEEOR")
                self.driver.quit()
                return False

    def __get_realtime_mes(self):
        """采集网易新闻热点的新闻链接及标题"""
        self.__get_url("https://news.163.com/")
        # 下滑到页面底部
        js = "window.scrollTo(0, document.body.scrollHeight)"
        self.driver.execute_script(js)  # 模拟鼠标滚轮，滑动页面至底部
        time.sleep(2)
        eles = self.driver.find_elements(By.XPATH, r"//div[@class='data_row news_article clearfix ']")
        news_urls = []
        titles = []
        for ele in eles:
            if self.__element_exist(r"./a", ele=ele, timeout=2):
                model = "01"
            else:
                model = "02"

            if model == "01":
                news_url = ele.find_element(By.XPATH, "./a").get_attribute("href")
                title = ele.find_element(By.XPATH, "./div/div").text
                stop_date = "1天前"
                try:
                    stop_date = ele.find_element(By.XPATH, ".//div[@class='news_tag']/span").text
                except Exception as e:
                    pass
                if "天前" in stop_date and int(stop_date.split("天前")[0]) > 3:
                    continue
            else:
                news_url = ele.find_element(By.XPATH, ".//a").get_attribute("href")
                title = ele.find_element(By.XPATH, ".//a").text
                stop_date = ele.find_element(By.XPATH, ".//div[@class='news_tag']/span").text

            news_urls.append(news_url)
            titles.append(title)

        return news_urls, titles

    def __web_new_mes(self, news_urls, titles):
        """根据新闻链接及标题，访问新闻页面，获取抽取标题及抽取正文"""
        if int(time.strftime("%H", time.localtime())) != self.realtime_hour:
            self.realtime_hour = int(time.strftime("%H", time.localtime()))
            realtime_id_first = time.strftime("%Y%m%d%H", time.localtime())[2:]  # 23031609表示23年3月16日9点
            self.realtime_id_num = 0
        else:
            realtime_id_first = time.strftime("%Y%m%d%H", time.localtime())[2:]  # 23031609表示23年3月16日9点

        unuse_url = 0
        for j, (url, title) in enumerate(zip(news_urls, titles)):
            for i in range(3):
                try:
                    order_dic = {"ArticleUrl": url}
                    if len(self.sqlserver.neteast_content_select(order_dic, mode="mode_00")) > 0:
                        unuse_url += 1
                        break
                    self.__get_url(url, sleep_time=4 + i * 2)
                    extract_title = self.driver.find_element(By.XPATH, "//h1[@class='post_title']").text
                    extract_content = self.driver.find_element(By.XPATH, "//div[@class='post_body']").text
                    article_time = self.driver.find_element(By.XPATH, "//div[@class='post_info']").text
                    article_time = article_time.split("来源")[0].strip()
                    publisher = self.driver.find_element(By.XPATH, "//div[@class='post_info']/a").text
                    realtime_id = realtime_id_first + "0" * (3 - len(str(self.realtime_id_num))) + str(self.realtime_id_num)  # 年月日编号
                    self.realtime_id_num += 1

                    html = self.driver.page_source  # 网页源码
                    path = os.path.join(self.work_dir, "html/ne{}.txt".format(realtime_id))
                    # print("这是地址1：{}".format(self.work_dir))
                    # print("这是地址：{}".format(path))
                    # file = open(path, "w", encoding="utf-8")
                    # file.write(html)
                    # file.close()

                    # 写入数据库
                    order_dic = {"RealtimeId": realtime_id,
                                 "Content": extract_content.replace("'", "\""),  # 避免正文过长插入出错
                                 "ArticleUrl": url,
                                 "ArticleTime": article_time,
                                 "Publisher": publisher,
                                 "Title": title.replace("'", "\""),
                                 "ExtractTitle": extract_title.replace("'", "\""),
                                 }

                    self.sqlserver.neteast_content_insert(order_dic, mode="mode_00")
                    break
                except Exception as e:
                    self.ner_log.write_in("提取信息出错，第{}次，url:{}".format(i, url))
        self.ner_log.write_in("单次检索条目{}，新条目{}".format(len(news_urls), len(news_urls) - unuse_url))

    def neteast_realtime(self):
        last_time = time.time() - 700
        while True:
            if time.time() - last_time < 600:  # 每十分钟采集一次
                time.sleep(60)
                continue
            self.ner_log.write_in("开始一次网易热搜采集")
            # 检测网络是否通畅，若出现环境问题则退出循环
            net_flag = self.__offline_check("https://www.baidu.com/")
            if not net_flag:
                break
            try:
                last_time = time.time()  # 执行采集后更新最后采集时间
                news_urls, titles = self.__get_realtime_mes()  # 获取标题及url

                self.__web_new_mes(news_urls, titles)  # 根据url采集最新的热点要闻

            except Exception as e:
                self.ner_log.write_in(traceback.format_exc(), level="ERROR")