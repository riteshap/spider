"""头条热搜"""
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


class TtWebGet:
    def __init__(self, work_dir, driver: webdriver.Chrome, net_mode="01"):
        self.driver = driver
        self.work_dir = work_dir
        self.pid = os.getpid()
        pickle.dump(self.pid, open("003_pid", "wb"))
        self.sqlserver = SqlServe(work_dir=self.work_dir)
        self.pas = PageAnalysis()
        self.config_path = os.path.join(self.work_dir, r"../config/config_main.ini")
        self.config = conf.ConfigParser()
        self.config.read(self.config_path, encoding="utf-8")
        self.net_mode = net_mode  # 01校园网，02互联网
        self.ttr_log = WriteLog(file_name="ttr_log", log_name="ttr", log_level="INFO")
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
            self.ttr_log.write_in("网络检查模式错误", level="WEEOR")
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
                    self.ttr_log.write_in("网络异常，无法正确登录", level="WEEOR")
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
                self.ttr_log.write_in("网络异常，无法正确登录", level="WEEOR")
                self.driver.quit()
                return False

    def __get_realtime_mes(self):
        self.__get_url("https://www.toutiao.com/")
        # 下滑到页面底部
        js = "window.scrollTo(0, 400)"
        self.driver.execute_script(js)  # 模拟鼠标滚轮，下滑400高度
        time.sleep(2)

        titles = []
        urls = []

        for i in range(10):  # 头条热搜往往是50条
            eles = self.driver.find_elements(By.XPATH, "//div[@class='ttp-hot-board']/ol/li/a")
            end_flag = True
            for ele in eles:
                title = ele.get_attribute("aria-label")
                url = ele.get_attribute("href")
                if title not in titles:
                    # sql查询14天内重复标题，若标题重复则跳过
                    order = {"Title": title}
                    out = self.sqlserver.toutiao_content_select(order, mode="mode_00")
                    if len(out) > 0:
                        continue
                    titles.append(title)
                    urls.append(url)
                    end_flag = False
            if end_flag and i > 2:
                break
            ele = self.driver.find_element(By.XPATH, "//div[@class='ttp-hot-board']/div[@class='title-bar']/button")
            ele.click()
            time.sleep(4)
        self.ttr_log.write_in("头条本次获取到新条目数量为：{}".format(len(urls)))
        return urls, titles

    def __web_new_mes(self, urls, titles):

        for i, (url, title) in enumerate(zip(urls, titles)):
            try:
                self.__get_url(url)
                cur_url = self.driver.current_url
                if "https://www.toutiao.com/article" in cur_url:
                    self.__get_article(cur_url, title)
                    time.sleep(7)
                elif "https://www.toutiao.com/trending" in cur_url:
                    for j in range(3):
                        if self.__element_exist("//div[@class='card-render-wrapper']/div/div/div/a"):
                            break
                        else:
                            time.sleep(5)
                            self.driver.refresh()
                            time.sleep(5)

                    eles = self.driver.find_elements(By.XPATH, "//div[@class='card-render-wrapper']/div/div/div/a")

                    article_urls = []
                    for ele in eles:
                        article_url = ele.get_attribute("href")
                        if "article" in article_url:
                            article_urls.append(article_url)

                    for article_url in article_urls:
                        self.__get_url(article_url)
                        self.__get_article(article_url, title)
                        time.sleep(7)

                    if len(article_urls) == 0:
                        time.sleep(5)
                else:
                    self.ttr_log.write_in("头条热搜出现未知模式：{}".format(cur_url))

            except Exception as e:
                time.sleep(15)
                continue

    def __get_article(self, article_url, title):
        for i in range(3):
            if self.__element_exist("//div[@class='article-content']/h1"):
                break
            else:
                time.sleep(5)
                self.driver.refresh()
                time.sleep(5)

        if int(time.strftime("%H", time.localtime())) != self.realtime_hour:
            self.realtime_hour = int(time.strftime("%H", time.localtime()))
            realtime_id_first = time.strftime("%Y%m%d%H", time.localtime())[2:]  # 23031609表示23年3月16日9点
            self.realtime_id_num = 0
        else:
            realtime_id_first = time.strftime("%Y%m%d%H", time.localtime())[2:]  # 23031609表示23年3月16日9点

        extract_title = self.driver.find_element(By.XPATH, "//div[@class='article-content']/h1").text
        extract_content = self.driver.find_element(By.XPATH, "//div[@class='article-content']/article").text
        article_time = self.driver.find_element(By.XPATH, "//div[@class='article-content']/div[@class='article-meta']/span[1]").text
        if len(article_time) < 5:  # 有时候前面会有一个“原创”标签，猜测也有可能会有别的标签
            article_time = self.driver.find_element(By.XPATH,
                                                    "//div[@class='article-content']/div[@class='article-meta']/span[2]").text
        publisher = self.driver.find_element(By.XPATH, "//div[@class='article-content']/div[@class='article-meta']/span[@class='name']").text

        realtime_id = realtime_id_first + "0" * (3 - len(str(self.realtime_id_num))) + str(
            self.realtime_id_num)  # 年月日编号
        self.realtime_id_num += 1

        html = self.driver.page_source  # 网页源码
        path = os.path.join(self.work_dir, "html/tt{}.txt".format(realtime_id))
        # file = open(path, "w", encoding="utf-8")
        # file.write(html)
        # file.close()

        # 插入sql
        order = {"RealtimeId": realtime_id,
                 "Title": title,
                 "ExtractTitle": extract_title.replace("'", "\""),
                 "Content": extract_content.replace("'", "\""),
                 "ArticleTime": article_time,
                 "Publisher": publisher,
                 "ArticleUrl": article_url,
                 }

        self.sqlserver.toutiao_content_insert(order, mode="mode_00")

    def toutiao_realtime(self):
        last_time = time.time() - 700
        while True:
            if time.time() - last_time < 600:  # 每十分钟采集一次
                time.sleep(60)
                continue
            # 检测网络是否通畅，若出现环境问题则退出循环
            net_flag = self.__offline_check("https://www.baidu.com/")
            if not net_flag:
                break
            try:
                urls, titles = self.__get_realtime_mes()

                self.__web_new_mes(urls, titles)

                last_time = time.time()  # 执行采集后更新最后采集时间
            except Exception as e:
                self.ttr_log.write_in(traceback.format_exc(), level="ERROR")