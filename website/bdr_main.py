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


class BdWebGet:
    def __init__(self, work_dir, driver: webdriver.Chrome, net_mode="01"):
        self.driver = driver
        self.work_dir = work_dir
        self.pid = os.getpid()
        pickle.dump(self.pid, open("001_pid", "wb"))
        self.sqlserver = SqlServe(work_dir=self.work_dir)
        self.pas = PageAnalysis()
        self.config_path = os.path.join(self.work_dir, r"../config/config_main.ini")
        self.config = conf.ConfigParser()
        self.config.read(self.config_path, encoding="utf-8")
        self.net_mode = net_mode  # 01校园网，02互联网
        self.bdr_log = WriteLog(file_name="bdr_log", log_name="bdr", log_level="INFO")
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
            self.bdr_log.write_in("网络检查模式错误", level="WEEOR")
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
                    self.bdr_log.write_in("网络异常，无法正确登录", level="WEEOR")
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
                self.bdr_log.write_in("网络异常，无法正确登录", level="WEEOR")
                self.driver.quit()
                return False

    def __c_grope_wrapper(self, wrapper, a_url, try_i, recollect):
        titles = wrapper.find_elements(By.XPATH,
                                       './/div[contains(@class,"render-item")]/div[contains(@class,"content")]')
        if len(titles) == 0:
            if try_i >= 2:
                raise Exception("百度搜索中获取资讯条目异常为空, recollect={}".format(recollect))
            else:
                if self.__element_exist(xpath='/div[1]//i[contains(@class,"video-play")]', ele=wrapper):
                    # 说明置顶为视频, 采集前三条常规搜索结果，
                    # 至少是有一条相关的，有时候相关的也只有一条
                    # 有时候第一条偏偏不相关，这些问题需要以后处理
                    self.bdr_log.write_in("置顶为视频, 需要加入重采, recollect={}".format(recollect))
                    raise Exception("置顶为视频, 需要加入重采, recollect={}".format(recollect))
                else:
                    # 置顶非视频,建议没咨询的也都加入重采，重采没信息的再采集第一条
                    # try:
                    #     title_obj = wrapper.find_element(By.XPATH, './div[1]//div[contains(@class,"text-container")]')
                    #     title = title_obj.find_element(By.XPATH, './p').get_attribute('aria-label')
                    #     bd_url = title_obj.find_element(By.XPATH, './p/a').get_attribute('href')
                    #     publisher_obj = title_obj.find_element(By.XPATH, '.// span[contains( @class ,"source-title")]')
                    #     publisher = publisher_obj.text  # 发文来源
                    #     order_dic = {"RealtimeId": a_url[1],  # RealtimeId
                    #                  "ArticleId": 0,
                    #                  "Title": title.replace("'", "\""),
                    #                  "Publisher": publisher,
                    #                  "BdUrl": bd_url
                    #                  }
                    #     self.sqlserver.baidu_content_insert(order_dic, mode="mode_00")
                    #     return True
                    # except Exception as e:
                    #     raise Exception("获取置顶文章链接出错")
                    self.bdr_log.write_in("置顶非视频, 无资讯故加入重采, recollect={}".format(recollect))
                    raise Exception("置顶非视频, 无资讯故加入重采, recollect={}".format(recollect))

        for ArticleId, abstract in enumerate(titles):
            title_obj = abstract.find_element(By.XPATH, "./a[1]")
            title = title_obj.text  # 标题
            bd_url = title_obj.get_attribute("href")  # 链接
            publisher_obj = abstract.find_element(By.XPATH, './a[2]/div/span')
            publisher = publisher_obj.text  # 发文来源

            order_dic = {"RealtimeId": a_url[1],  # RealtimeId
                         "ArticleId": ArticleId,
                         "Title": title.replace("'", "\""),
                         "Publisher": publisher,
                         "BdUrl": bd_url
                         }
            self.sqlserver.baidu_content_insert(order_dic, mode="mode_00")
            return True

    def __pos_wrapper(self, wrapper, a_url):
        title = wrapper.find_element(By.XPATH, ".//p").text
        bd_url = wrapper.find_element(By.XPATH, ".//p/a").get_attribute("href")
        publisher = wrapper.find_element(By.XPATH, ".//div[contains(@class,'source-wrapper')]/a/span").text

        order_dic = {"RealtimeId": a_url[1],  # RealtimeId
                     "ArticleId": 0,
                     "Title": title.replace("'", "\""),
                     "Publisher": publisher,
                     "BdUrl": bd_url,
                     }
        self.sqlserver.baidu_content_insert(order_dic, mode="mode_00")

    def __bd_new_url(self, new_url: list, recollect=False):
        """
        在热搜首页检索后，对于新增加的热搜条目的url进行遍历，获取百度首页搜索结果
        此步骤可能触发百度反爬虫，需要继续观察
        获取的条目基本信息存储在数据库中
        """
        # new_url遍历，检索新闻正文详情
        for a_url in new_url:
            collect_flag = False
            for i in range(3):
                class_name = "None"
                try:
                    self.__get_url(a_url[0], sleep_time=2 + i * 2)
                    if i > 0:  # 向下翻动一定的页面
                        js = "window.scrollTo(0, 600)"
                        self.driver.execute_script(js)  # 模拟鼠标滚轮，滑动页面至底部
                        time.sleep(2)

                    all_wrapper = ["c-group-wrapper", "single-card-wrapper", "weak-wrapper", "pos-wrapper",
                                   "image-wrapper", "button-wrapper", "list-wrapper"]
                    weak_wrapper = ["weak-wrapper"]

                    # c-group-wrapper
                    wrapper_a = '//*[@id="content_left"]/div[contains(@class,"wrapper")]'
                    # single-card-wrapper
                    wrapper_b = '//*[@id="content_left"]/div/div/div/div[contains(@class,"wrapper")]'
                    # pos-wrapper
                    wrapper_c = '//*[@id="content_left"]/div/div[contains(@class,"wrapper")]'
                    if self.__element_exist(xpath=wrapper_a):
                        wrapper = self.driver.find_element(By.XPATH, wrapper_a)
                    elif self.__element_exist(xpath=wrapper_b):
                        wrapper = self.driver.find_element(By.XPATH, wrapper_b)
                    elif self.__element_exist(xpath=wrapper_c):
                        wrapper = self.driver.find_element(By.XPATH, wrapper_c)
                    else:
                        wrapper = self.driver.find_element(By.XPATH,
                                                           '//*[@id="content_left"]//div[contains(@class,"wrapper")]')
                        wrapper_name = wrapper.get_attribute("class")
                        wrapper_name = wrapper_name.replace(" ", "").replace("\n", "")
                        self.bdr_log.write_in("加入等待重采，wrapper检测名：{}；检测不存在：{}".format(wrapper_name, a_url))
                        collect_flag = False
                        break

                    # 获取所有咨询窗格
                    class_name = wrapper.get_attribute("class")
                    if "pos-wrapper" in class_name:
                        self.__pos_wrapper(wrapper, a_url)
                    elif "c-group-wrapper" in class_name or "single-card-wrapper" in class_name:
                        self.__c_grope_wrapper(wrapper, a_url, i, recollect)
                    else:
                        self.bdr_log.write_in("出现意外未知wrapper{},{}".format(class_name, a_url))

                    time.sleep(random.randint(5, 10))
                    collect_flag = True
                    break  # 能够正常运行到最后则退出循环

                except Exception as e:
                    time.sleep(random.randint(5, 10))
                    self.bdr_log.write_in("第{}次采集尝试出现错误，{}：url:{}; class_name:{};"
                                          .format(i, traceback.format_exc(), a_url[0], class_name.replace("\n", " ")))
                    continue

            if collect_flag is False and recollect is False:  # 采集失败且非二次采集时
                # 该热搜太热乎，百度上还没生成对应的咨询，需要等待半小时再查询插入
                order = {"RealtimeId": a_url[1], "BdUrl": a_url[0]}
                self.sqlserver.baidu_recollect_insert(order, mode="mode_00")
                self.bdr_log.write_in("二次采集新增一条：{}".format(a_url[1]))

    def __web_new_mes(self):
        """
        从数据库检索未获取页面内容的新闻链接，以正文为空为标志
        访问具体页面，用gne解析正文，存入数据库，然后填充采集时间
        """
        order_dic = {}
        ret_list = self.sqlserver.baidu_content_select(order_dic, mode="mode_00")
        for ret in ret_list:
            if ret["BdUrl"] is None:  # url为空，回填正文collect failed
                order_dic = {"RealtimeId": ret["RealtimeId"]}
                self.sqlserver.baidu_content_update(order_dic, mode="mode_00")
                continue
            # 逐个url实现采集
            for i in range(3):
                try:
                    self.__get_url(ret["BdUrl"])

                    ArticleUrl = self.driver.current_url
                    print(ArticleUrl)
                    if ArticleUrl.startswith("https://baijiahao"):
                        # 百家号新闻手动解析即可
                        ExtractTitle = self.driver.find_element(By.XPATH, "//div[@id='header']/div").text
                        content = self.driver.find_element(By.XPATH, "//div[@data-testid='article']").text
                        ArticleTime = self.driver.find_element(By.XPATH, "//span[@data-testid='updatetime']").text
                    else:
                        source_html = self.driver.page_source
                        result = self.pas.analysis(source_html)
                        ExtractTitle = self.pas.title_extract(source_html, ret["Title"])
                        content = result["content"]
                        ArticleTime = time.strftime("%Y-%m-%d, %H:%M:%S")  # 设置为当前时间
                        # 回填信息

                    # html = self.driver.page_source  # 网页源码
                    # path = os.path.join(self.work_dir, "html/bd{}_{}.txt".format(ret["RealtimeId"], ret["ArticleId"]))
                    # file = open(path, "w", encoding="utf-8")
                    # file.write(html)
                    # file.close()

                    order_dic = {"RealtimeId": ret["RealtimeId"],
                                 "ArticleId": ret["ArticleId"],
                                 "Content": content.replace("'", "\""),  # 避免正文过长插入出错
                                 "ArticleUrl": ArticleUrl,
                                 "ExtractTitle": ExtractTitle.replace("'", "\""),
                                 "ArticleTime": ArticleTime}
                    self.sqlserver.baidu_content_update(order_dic, mode="mode_01")  # 回填正文和采集时间
                    break
                except Exception as e:
                    self.bdr_log.write_in("单一网页访问出现错误：{}".format(ret["BdUrl"]))
                    time.sleep(i * 5 + 5)

    def __get_realtime_mes(self):
        """采集百度热搜，每10分钟一次"""
        self.__get_url(aim_url=r"https://top.baidu.com/board?tab=realtime")
        # 下滑到页面底部
        js = "window.scrollTo(0, document.body.scrollHeight)"
        self.driver.execute_script(js)  # 模拟鼠标滚轮，滑动页面至底部
        time.sleep(2)

        eles = self.driver.find_elements(By.XPATH,
                                         value=r"//div[@id='sanRoot'][@theme='realtime']/main/div[2]/div/div[2]/div")
        self.bdr_log.write_in("本次检测到的热搜总数为:{}".format(len(eles)))

        if int(time.strftime("%H", time.localtime())) != self.realtime_hour:
            self.realtime_hour = int(time.strftime("%H", time.localtime()))
            realtime_id_first = time.strftime("%Y%m%d%H", time.localtime())[2:]  # 23031609表示23年3月16日9点
            self.realtime_id_num = 0
        else:
            realtime_id_first = time.strftime("%Y%m%d%H", time.localtime())[2:]  # 23031609表示23年3月16日9点

        new_url = []
        for i, ele in enumerate(eles):
            title = ele.find_element(By.XPATH, value="./div[2]/a/div").text.replace("\'", "\"")
            search_url = ele.find_element(By.XPATH, value="./div[2]/a").get_attribute("href")
            abstract = ele.find_element(By.XPATH, value="./div[2]/div[2]").text
            abstract = abstract[:-5].replace("\'", "\"")  # 最后几个字是“查看更多”
            realtime_id = realtime_id_first + "0" * (3 - len(str(self.realtime_id_num))) + str(
                self.realtime_id_num)  # 年月日编号
            self.realtime_id_num += 1
            order_dic = {"RealtimeId": realtime_id,
                         "Title": title.replace("'", "\""),
                         "Abstract": abstract,
                         "SearchUrl": search_url,
                         }
            # 检查每一条条目是否已存在于数据库中
            ret_list = self.sqlserver.baidu_realtime_select(order_dic, mode="mode_01")
            if len(ret_list) > 0:
                continue
            # 不存在则插入数据库
            self.sqlserver.baidu_realtime_insert(order_dic, mode="mode_01")  # 插入条目
            new_url.append([search_url, realtime_id])
        self.bdr_log.write_in("百度热搜新增条目数量:{}".format(len(new_url)))

        return new_url

    def __bd_recollect(self):
        order_list = self.sqlserver.baidu_recollect_select({}, mode="mode_00")
        if len(order_list) == 0:
            return None
        new_url = []
        for order in order_list:
            new_url.append([order["BdUrl"], order["RealtimeId"]])
            self.sqlserver.baidu_recollect_update({"RealtimeId": order["RealtimeId"]}, mode="mode_00")
        # 二次处理后，无论结果如何，将这些链接状态设置为True，也就是不再三次采集
        self.__bd_new_url(new_url, recollect=True)

    def baidu_realtime(self):
        """控制采集逻辑"""
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
                last_time = time.time()  # 执行采集后更新最后采集时间
                new_url = self.__get_realtime_mes()  # 采集热搜界面概述
                self.__bd_new_url(new_url)  # 根据热搜单一链接，采集百度中搜索出的内容

                self.__web_new_mes()  # 根据百度搜索出的内容，采集具体的文章链接

                self.__bd_recollect()  # 处理新上热搜无法采集到咨询的问题，新上热搜半小时后二次采集
            except Exception as e:
                self.bdr_log.write_in(traceback.format_exc(), level="ERROR")


if __name__ == "__main__":
    work_dir = os.getcwd()
    driver = webdriver.Chrome()
    aa = BdWebGet(work_dir, driver)
    aa.baidu_realtime()

