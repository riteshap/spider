from lxml.html import etree

class NePageAnalysis:
    def __init__(self):
        pass

    def analysis(self, html):
        root = etree.HTML(html)  # 解析源码
