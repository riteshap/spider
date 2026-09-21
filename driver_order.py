import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
# from website.bdr_main import BdWebGet
from website.wbr_main import WbWebGet
from website.ner_main import NeWebGet
from website.ttr_main import TtWebGet
from write_log import WriteLog
import os
import sys
import inspect
import platform
import configparser as conf


class DriverProcess:
    def __init__(self):
        self.work_dir = os.path.dirname(os.path.realpath(inspect.getfile(inspect.currentframe())))
        if "Windows" in platform.platform():
            config_model = "ord_main_win"
        else:
            config_model = "ord_main_linux"
        self.mode = sys.argv[1] if len(sys.argv) >= 2 else "000"  # 确定当前执行的网站名称

        self.config = conf.ConfigParser()
        self.config_path = os.path.join(self.work_dir, r"./config/config_order.ini")
        self.config.read(self.config_path, encoding="utf-8")
        self.user_data_dir = self.config.get(config_model, "user_data_dir{}".format(self.mode))
        self.chrome_driver = self.config.get(config_model, "chrome_driver")
        self.chrome_driver = os.path.join(self.work_dir, r"./driver/{}".format(self.chrome_driver))
        self.headless = self.config.get(config_model, "headless")

        self.driver = self.chrome_explorer(self.work_dir)
        self.net_mode = self.config.get(config_model, "net_mode")
        self.main_log = WriteLog(file_name="driver_log", log_name="driver", log_level="INFO")
        self.main_log.write_in("进程启动:{}，根目录地址：{}".format(os.getpid(), self.work_dir))

    def chrome_explorer(self, work_dir):
        chrome_options = Options()
        if self.headless == "True":
            chrome_options.add_argument('--headless')
        else:
            pass
        # options.add_argument('--incognito')  # 隐身模式（无痕模式）
        chrome_options.add_argument(r'user-data-dir={}'.format(self.user_data_dir))  # chrome://version/
        chrome_options.add_argument('--disable-gpu')  # 禁用gpu
        chrome_options.add_argument('--disable-infobars')  # 禁用浏览器正在被自动化程序控制的提示
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument('--no-sandbox')  # root用户不加这条会无法运行
        chrome_options.add_argument('--ignore-certificate-errors')  # 忽略证书错误
        chrome_options.add_argument('--allow-insecure-localhost')  # 忽略本地TLS和SSL错误
        # chrome_options.add_argument('--ignore-ssl-errors')  # 忽略ssl错误，不好使，需要配合switch两条关闭错误提示
        # chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        # chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        # chrome_options.add_argument('--disable-blink-features=AutomationControlled')  # 关闭自动控制blink特征
        # chrome_options.binary_location = "./Chrome/Application{}/chrome.exe".format(self.model)
        # 百度热搜、贴吧热议不要图片，微博要图片，头条不要图片
        if self.mode not in ["000", "001"]:
            prefs = {'profile.default_content_setting_values': {'images': 2}}  # 不加载图片
            chrome_options.add_experimental_option('prefs', prefs)
        chrome_service = Service(self.chrome_driver)
        driver = webdriver.Chrome(options=chrome_options, service=chrome_service)

        driver.set_page_load_timeout(10)
        driver.set_script_timeout(10)
        width = 1400
        height = 1000
        driver.set_window_size(width, height)
        time.sleep(2)
        return driver

    def weibo_realtime(self):
        bd_main = WbWebGet(self.work_dir, self.driver, self.net_mode)
        bd_main.weibo_realtime()

    def neteast_realtime(self):
        ne_main = NeWebGet(self.work_dir, self.driver, self.net_mode)
        ne_main.neteast_realtime()

    def toutiao_realtime(self):
        ne_main = TtWebGet(self.work_dir, self.driver, self.net_mode)
        ne_main.toutiao_realtime()

    def main(self):

        if self.mode == "000":
            self.weibo_realtime()  # 默认模式，用于测试,暂时废弃百度热搜采集
        elif self.mode == "001":
            self.weibo_realtime()
        elif self.mode == "002":
            self.neteast_realtime()
        elif self.mode == "003":
            self.toutiao_realtime()
        else:
            print("模式不存在，子进程启动失败")

    def test_fun(self):
        """该函数仅用作测试"""
        import time
        self.driver.get("https://www.baidu.com/")
        js = "window.scrollTo(0, 600)"
        self.driver.execute_script(js)  # 模拟鼠标滚轮，滑动页面至底部
        time.sleep(2)


if __name__ == "__main__":
    DP = DriverProcess()
    DP.main()
    # DP.test_fun()



