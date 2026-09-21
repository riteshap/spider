import os, sys
import logging
from logging.handlers import TimedRotatingFileHandler


class WriteLog:
    def __init__(self, file_name: str, log_name="main", log_level="DEBUG"):
        self.DEBUG = "DEBUG"
        self.INFO = "INFO"
        self.WARNING = "WARNING"
        self.ERROR = "ERROR"
        logging_level = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR
        }

        self.logger = logging.getLogger(log_name)  # 打印时的抬头
        self.logger.setLevel(logging_level[log_level])  # 设置日志等级
        self.dir_path = os.path.join(os.path.split(sys.argv[0])[0], 'log')
        self.log_path = os.path.join(self.dir_path, file_name).replace('\\', '/')
        if not os.path.exists(self.dir_path):  # 若不存在该日志保存路径则创造该路径
            os.makedirs(self.dir_path)
        # 输出到文件
        fh = TimedRotatingFileHandler(filename=self.log_path, when="D", interval=1, backupCount=2, encoding="utf-8")
        sh = logging.StreamHandler(sys.stdout)  # 输出到屏幕
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(process)d - %(levelname)s - %(message)s")
        fh.setFormatter(formatter)  # 设置输出格式
        sh.setFormatter(formatter)  # 设置输出格式
        if len(self.logger.handlers) < 2:
            self.logger.addHandler(fh)
            self.logger.addHandler(sh)
        else:
            pass

    def write_in(self, message, level="INFO"):
        if level == self.DEBUG:
            self.logger.debug(message)
        elif level == self.INFO:
            self.logger.info(message)
        elif level == self.WARNING:
            self.logger.warning(message)
        elif level == self.ERROR:
            self.logger.error(message)
        else:
            self.logger.critical(message)

"""
if __name__ == "__main__":
    print("hello")
    s = WriteLog("log")
"""