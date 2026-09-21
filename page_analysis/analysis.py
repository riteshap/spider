"""
分析单页面标题及正文
"""
import re
import time

from lxml.html import etree
from gne import GeneralNewsExtractor


class PageAnalysis:
    def __init__(self):
        self.extractor = GeneralNewsExtractor()

    def __process_all_text_node(self, txt_node):
        all_text_node = []  # 记录所有文字节点
        for one_node in txt_node:
            if len(re.sub("\s", "", one_node)) < 2:  # 去除空白字符
                continue

            try:
                cur_node = one_node.getparent()  # 可能存在父节点不是正常节点
                # print(type(cur_node))
                if str(type(cur_node)) == "<class 'lxml.etree._Element'>" and cur_node.tag in ["script", "style", "noscript"]:
                    continue

                # new_xpath = "//" + root_tree.getelementpath(cur_node)
                # obj = self.driver.find_element_by_xpath(new_xpath)
            except Exception as e:
                continue
            # print(one_node)

            # size = obj.value_of_css_property('font-size')
            # all_text_node.append([new_xpath, size.split("px")[0], len(re.sub("\s", "", one_node))])
            all_text_node.append(one_node)
        return all_text_node

    def analysis(self, html):
        result = self.extractor.extract(html)

        return result

    def title_extract(self, html, title: str):
        if not title.endswith("..."):  # 若不是以...结尾，那么直接返回原始title
            return title
        """对于以三个点结尾的缩减标题，要从正文页面上再重新提取标题"""
        html = re.sub('</?br.*?>', '', html)
        html = re.sub("<head>.*?</head>", "", html, count=1, flags=re.DOTALL)
        root = etree.HTML(html)  # 解析源码
        root_tree = root.getroottree()  # 生成树
        txt_node = root.xpath("//text()")
        all_text_node = self.__process_all_text_node(txt_node)  # 获取所有文字节点
        """可能存在标题处于两个节点下的情况，暂时先不处理"""
        title = title[:-3]  # 去除最后三个省略号
        if title.startswith("..."):
            title = title[3:]
        punctuation = "[!,.?:'\"()！，。？：‘“（）]"
        c_title = re.sub("\s", "", title)
        c_title = re.sub(punctuation, "", c_title)
        ret_title = "*" * 200
        for t_node in all_text_node:
            # 百度热搜会将中文字符标点转换为英文的，因此需要去除标点再对比
            st = re.sub("\s", "", t_node)
            c_st = re.sub(punctuation, "", st)
            if c_title in c_st and len(c_st) < len(ret_title):
                # 刷爆热搜！中国女篮夺冠嗨翻天 韩旭现场跳舞 李梦激动落泪
                # '刷爆热搜中国女篮夺冠嗨翻天 韩旭现场跳舞 李梦激'
                ret_title = st
        if len(ret_title) == 200:  # 未能识别到正确的tilte
            return title + "..."
        else:
            return ret_title


if __name__ == "__main__":
    from selenium import webdriver

    driver = webdriver.Chrome()
    driver.get("https://finance.sina.com.cn/jjxw/2023-07-04/doc-imyzpftp4034742.shtml")
    time.sleep(2)
    page_source = driver.page_source
    cls = PageAnalysis()
    title = "刷爆热搜!中国女篮夺冠嗨翻天 韩旭现场跳舞 李梦激..."
    cls.title_extract(page_source, title)
