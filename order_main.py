"""
主进程，控制子进程启停
1.微博热搜；2.网易热搜；3.头条热搜；4.贴吧热议；5.知乎热搜；
1.重点目标：微博认证账号、微信公众号
chrome://flags/
chrome://version
"""
import os
import sys
import time
import inspect
import subprocess
import platform
import psutil
import pickle
from write_log import WriteLog
from SqlServe import SqlServe


class MainProcess:
    def __init__(self):
        self.main_log = WriteLog(file_name="main_log", log_name="main", log_level="INFO")
        work_dir = os.path.dirname(os.path.realpath(inspect.getfile(inspect.currentframe())))
        self.sqlserver = SqlServe(work_dir=work_dir)

    def single_process(self, mission_id):
        cmd = "python ./driver_order.py {}".format(mission_id)
        if "Windows" in platform.platform():
            shell_model = False
        else:
            shell_model = True
        __prog = subprocess.Popen(cmd, shell=shell_model)
        return __prog.pid

    # def single_process2(self, mission_id):
    #     cmd = "python ./driver_order.py {}".format(mission_id)
    #
    #     __prog = subprocess.Popen(cmd)
    #     return __prog.pid

    def DingTalk(self, mes):
        import requests
        import json
        # 钉钉机器人Webhook地址
        webhook = 'https://oapi.dingtalk.com/robot/send?access_token=5761b29265fb4bd9e7ff79eae665b2fbaf12f0b619ec1852f233626c0dfb16c2'
        # 构建请求头部
        header = {
            "Content-Type": "application/json",
            "Charset": "UTF-8"
        }
        # 构建请求数据
        text_message = {
            "msgtype": "text",
            "at": {
                "atMobiles": [],
                "isAtAll": False
            },
            "text": {
                "content": "数采:{}".format(mes)
            }
        }
        # 发送请求
        response = requests.post(url=webhook, headers=header, data=json.dumps(text_message))
        # 打印返回结果
        # print(response.text)

    def timming_mission(self, begin_time, immediately=False):  # 定时任务都放在这里
        """
        程序定时任务，目前分为零点切换日期的定时任务、小时时间切换的定时任务
        每一项任务用try/except分隔，无用任务的垃圾回收通常作为定时任务记录于此函数
        """
        if "python" in str(sys.executable):  # 直接以py脚本方式运行
            work_dir = os.path.dirname(os.path.realpath(inspect.getfile(inspect.currentframe())))
        else:
            work_dir = os.path.dirname(os.path.realpath(sys.executable))

        if int(time.strftime("%d", time.localtime())) != begin_time["DAY"] or immediately:  # 说明零点更换了日期
            begin_time["DAY"] = int(time.strftime("%d", time.localtime()))

    def main(self):
        """主进程，控制进度"""
        mission_dic = {"001": "微博热搜",
                       "002": "网易热搜",
                       "003": "头条热搜",
                       "004": "贴吧热议",
                       "005": "知乎热搜"}
        pid_dic = {"001": 0, "002": 0, "003": 0}  # 用于管理已经上线的爬取模块
        self.main_log.write_in(mission_dic)
        for order in pid_dic.keys():
            pid = self.single_process(order)
            self.main_log.write_in("启动{}进程：{}".format(mission_dic[order], pid))
            time.sleep(10)
            # 子进程会保存一个pid文件用于记录进程号
            pid_dic[order] = pickle.load(open("{}_pid".format(order), "rb"))
        self.main_log.write_in("全进程pid字典：{}".format(pid_dic))

        begin_time = {"HOUR": int(time.strftime("%H", time.localtime()))}
        while True:
            if int(time.strftime("%H", time.localtime())) != begin_time["HOUR"]:
                begin_time["HOUR"] = int(time.strftime("%H", time.localtime()))
                out_data_bd = ""
                # out_data_bd = self.sqlserver.baidu_content_select({}, mode="mode_01")
                out_data_ne = self.sqlserver.neteast_content_select({}, mode="mode_01")
                out_data_tt = self.sqlserver.toutiao_content_select({}, mode="mode_01")
                self.DingTalk("BD新增条目：{};NE新增条目：{};TT新增条目：{}"
                              .format(len(out_data_bd), len(out_data_ne), len(out_data_tt)))
            for pid_k in pid_dic.keys():
                if pid_dic[pid_k] not in psutil.pids():
                    self.main_log.write_in("{}进程退出, 需要重启".format(mission_dic[pid_k]))
                    time.sleep(600)
                    pid = self.single_process(pid_k)
                    self.main_log.write_in("重新启动{}进程：{}".format(mission_dic[pid_k], pid))
                    self.DingTalk("重新启动{}进程：{}".format(mission_dic[pid_k], pid))
                    time.sleep(10)
                    pid_dic[pid_k] = pickle.load(open("{}_pid".format(pid_k), "rb"))
            self.main_log.write_in("现存进程号如下：{}".format(pid_dic))
            time.sleep(100)


if __name__ == "__main__":
    MP = MainProcess()
    MP.main()


