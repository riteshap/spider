"""预测模型用，用于从网页中根据指定xpath获取所有子节点信息，用于判断正文所在位置"""

from lxml.html import etree
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import inspect
import time
import re
import copy


class WebGet:
    def __init__(self, aim_url):
        chrome_options = Options()
        # chrome_options.add_argument('--headless')
        # chrome_options.add_argument('--disable-gpu')
        # chrome_options.add_argument('--no-sandbox')  # root用户不加这条会无法运行
        prefs = {'profile.default_content_setting_values': {'images': 2}}  # 不加载图片
        chrome_options.add_experimental_option('prefs', prefs)
        path = os.path.dirname(os.path.realpath(inspect.getfile(inspect.currentframe())))
        self.driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=os.path.join(path, "../chromedriver.exe"))

        self.driver.set_page_load_timeout(10)
        self.driver.set_script_timeout(10)
        self.text_num = 0
        self.width = 1400
        self.height = 1000
        self.driver.set_window_size(self.width, self.height)
        self.replace_url(aim_url)
        # try:
        #     self.driver.get(aim_url)
        #     time.sleep(1)
        # except Exception as e:
        #     try:
        #         self.driver.execute_script("window.stop()")
        #     except:
        #         pass
        # source_code = copy.deepcopy(self.driver.page_source)
        #
        # source_code = re.sub("<head>.*?</head>", "", source_code, count=1, flags=re.DOTALL)  # 去除head节点干扰
        #
        # obj = self.driver.find_element_by_xpath('//body')
        # self.page_height = obj.rect["height"]
        # self.page_width = obj.rect["width"]
        # if self.page_width == 0:
        #     self.page_width = self.width
        # if self.page_height == 0:
        #     raise Exception("页面读取大小出错")  # 后续再处理此类网页
        #
        # self.root = etree.HTML(source_code)  # 解析源码
        # self.root_tree = self.root.getroottree()  # 生成树
        # self.txt_node = self.root.xpath("//text()")
        # self.all_text_node = self.get_all_text_node()  # 获取所有文字节点

    def find_xpath(self, xpath):
        """测试用，寻找页面指定xpath"""
        objs = self.driver.find_elements_by_xpath(xpath)
        aim_node = self.root_tree.find(xpath)

        return aim_node

    def replace_url(self, aim_url):
        try:
            self.driver.get(aim_url)
            time.sleep(2)
        except Exception as e:
            try:
                self.driver.execute_script("window.stop()")
            except:
                pass
        source_code = self.driver.page_source

        source_code = re.sub("<head>.*?</head>", "", source_code, count=1, flags=re.DOTALL)  # 去除head节点干扰

        obj = self.driver.find_element_by_xpath('//body')
        self.page_height = obj.rect["height"]
        self.page_width = obj.rect["width"]
        if self.page_width == 0:
            self.page_width = self.width

        self.root = etree.HTML(source_code)  # 解析源码
        self.root_tree = self.root.getroottree()  # 生成树
        self.txt_node = self.root.xpath("//text()")
        self.all_text_node = self.get_all_text_node()  # 获取所有文字节点
        if len(self.all_text_node) < 5:
            raise Exception("页面文本过少，需要人工处理")

        if self.page_height < 300:
            # 从所有文字节点中读取最后5个节点，选择最大的y值作为页面高
            max_height = 0
            for node in self.all_text_node[-4:]:
                try:
                    obj = self.driver.find_element_by_xpath(node[0])
                    obj_rect = obj.rect
                except Exception as e:
                    continue
                if obj_rect["y"] > max_height:
                    max_height = obj_rect["y"]

            if max_height > 0:
                self.page_height = max_height

        if self.page_height == 0:
            raise Exception("页面读取大小出错")  # 后续再处理此类网页

    def get_all_text_node(self):
        all_text_node = []  # 记录所有文字节点
        # 清洗原始text_node,最后用于匹配文本节点获取是否完整
        new_text_node = []
        for one_node in self.txt_node:
            if len(re.sub("\s", "", one_node)) < 2:  # 去除空白字符
                continue
            new_text_node.append(one_node)

        self.txt_node = new_text_node
        self.text_num = 0
        for one_node in self.txt_node:
            try:
                cur_node = one_node.getparent()
                if cur_node.tag in ["script", "style", "noscript"]:
                    continue
                self.text_num += 1  # 用于对比最终识别出的文本数目是否足够，all_text_node中文本过少则认为页面解析出错

                new_xpath = "//" + self.root_tree.getelementpath(cur_node)
                obj = self.driver.find_element_by_xpath(new_xpath)
            except Exception as e:
                continue
            # print(one_node)

            size = obj.value_of_css_property('font-size')
            all_text_node.append([new_xpath, size.split("px")[0], len(re.sub("\s", "", one_node)), one_node])
        return all_text_node

    def get_content(self, content_xpath):
        """根据xpath返回识别结果"""
        content = ""
        for node in self.all_text_node:
            aim_content_xpath = re.sub("\[1]", "", content_xpath)  # 避免xpath中的[1]号节点带来的干扰
            aim_node_path = re.sub("\[1]", "", node[0])

            if aim_content_xpath != aim_node_path[:len(aim_content_xpath)]:
                continue

            if aim_content_xpath == aim_node_path:
                pass
            elif aim_node_path[len(aim_content_xpath)] == "[":
                continue

            content += node[3]

        return content

    def check_size(self, level_xpath):
        """根据给定xpath，计算返回指定xpath节点下占比最多的字号大小和占比, [1]匹配存在问题"""
        statistic = {}
        for node in self.all_text_node:
            aim_level_xpath = re.sub("\[1]", "", "//" + level_xpath)  # 避免xpath中的[1]号节点带来的干扰
            aim_node_path = re.sub("\[1]", "", node[0])

            if aim_level_xpath != aim_node_path[:len(aim_level_xpath)]:
                continue
            elif aim_level_xpath == aim_node_path:
                pass
            elif aim_node_path[len(aim_level_xpath)] == "[":
                continue

            statistic[node[1]] = statistic.get(node[1], 0) + node[2]

        if len(statistic) == 0:
            return 0, 0
        # 计算出最大的字号
        max_size = ""
        max_num = 0
        for key in statistic.keys():
            if statistic[key] > max_num:
                max_num = statistic[key]
                max_size = key

        proportion = max_num / sum(statistic.values())

        return round(float(max_size), 4), round(proportion, 4)

    def check_child_node(self, node_xpath, level):
        """用于返回包含正文节点的子节点数据，父节点为宽或高为0的节点"""
        if level > 2:  # 达到第二层及以下不再继续迭代
            return []
        cur_node = self.root_tree.find(node_xpath)
        page_obj_dic = []
        for node in cur_node:
            if node.tag in ["script", "style", "noscript"]:
                continue
            try:
                node_xpath = self.root_tree.getelementpath(node)  # 可能导致某些层级节点消失，需要在训练数据生成时注意
                obj = self.driver.find_element_by_xpath("//" + node_xpath)  # 可能识别出一些根本不存在的节点
                obj_rect = obj.rect
            except Exception as e:
                continue
            if obj_rect["width"] == 0 or obj_rect["height"] == 0:
                add_page_obj_dic = self.check_child_node(node_xpath, level=level + 1)
                page_obj_dic.extend(add_page_obj_dic)
                continue
            max_size, proportion = self.check_size(node_xpath)  # 最大字号，概率占比
            if max_size == 0:
                continue
            obj_dic = self.get_rect("//" + node_xpath, obj_rect, max_size, proportion)
            page_obj_dic.append(obj_dic)

        return page_obj_dic

    def get_rect(self, node_xpath, obj_rect, max_size, proportion):
        obj_dic = {}
        obj_dic["x"] = round((obj_rect["x"] + obj_rect["width"] / 2) / self.page_width, 4)
        obj_dic["y"] = round((obj_rect["y"] + obj_rect["height"] / 2) / self.page_height, 4)
        obj_dic["width"] = round(obj_rect["width"] / self.page_width, 4)
        obj_dic["height"] = round(obj_rect["height"] / self.page_height, 4)

        obj_dic["max_size"] = max_size / 100
        obj_dic["proportion"] = proportion

        obj_dic["xpath"] = node_xpath  # 当前节点的xpath

        return obj_dic

    def get_nodes_rect(self, content_xpath="//body"):
        cur_node = self.root_tree.find(content_xpath)
        father_obj = self.driver.find_element_by_xpath(content_xpath)  # 可能识别出一些根本不存在的节点,对br节点则会识别错误
        father_obj_rect = father_obj.rect

        page_obj_dic = []
        for node in cur_node:
            if node.tag in ["script", "style", "noscript"]:
                continue
            try:
                node_xpath = self.root_tree.getelementpath(node)  # 可能导致某些层级节点消失，需要在训练数据生成时注意
                obj = self.driver.find_element_by_xpath("//" + node_xpath)  # 可能识别出一些根本不存在的节点
                obj_rect = obj.rect
                if "br" in node_xpath.split("/")[-1] and node.tail is not None and len(re.sub("\s", "", node.tail)) > 1:
                    obj_rect["height"] = father_obj_rect["height"] / 4  # 这里处理的不好
                    obj_rect["width"] = father_obj_rect["width"]
            except Exception as e:
                continue

            if obj_rect["x"] < 0 or obj_rect["y"] < 0:  # 非正常节点
                continue

            if obj_rect["width"] <= 0 or obj_rect["height"] <= 0:
                # 若无法识别宽高的节点包含正文节点，则需要把该节点下的一级子节点加入，作为当前层级节点
                add_page_obj_dic = self.check_child_node(node_xpath, level=1)
                page_obj_dic.extend(add_page_obj_dic)
                continue

            max_size, proportion = self.check_size(node_xpath)  # 最大字号，概率占比

            if max_size == 0:
                continue

            obj_dic = self.get_rect("//" + node_xpath, obj_rect, max_size, proportion)

            page_obj_dic.append(obj_dic)  # 如果只有一个子节点，则在识别环节要跳过

        return page_obj_dic


if __name__ == "__main__":
    web_class = WebGet("http://wenshan.yunnan.cn/system/2021/05/07/031435366.shtml")
    # web_class = WebGet("http://www.chinaqw.com/sp/2021/05-06/294978.shtml")
    # http://yuqing.jschina.com.cn/shgl/202105/t20210506_2775811.shtml
    # http://www.kunlunce.com/ssjj/fl1/2021-05-10/152182.html

    # aim_node = web_class.find_xpath("//body/div[1]/div[2]/div[1]/ul/li/a")
    obj = web_class.driver.find_element_by_xpath("//body/div[6]/div[1]/div[3]/div/div[4]")
    px_size = obj.value_of_css_property('font-size')
    page_obj_dic = web_class.get_nodes_rect("//body")

    content = web_class.get_content("//body")

    print("over")
    pass