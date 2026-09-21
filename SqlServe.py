import os
import pymysql
import traceback
import configparser as conf
from write_log import WriteLog


class SqlServe:
    """
    增删改查，各个表对应不同函数
    """
    def __init__(self, work_dir):
        self.config_path = os.path.join(work_dir, r"./config/configSQL.ini")
        self.config = conf.ConfigParser()
        self.config.read(self.config_path, encoding="utf-8")
        self.__ip = self.config.get("DataBase", "ip")
        self.__account = self.config.get("DataBase", "account")
        self.__pwd = self.config.get("DataBase", "passwd")
        self.__db = self.config.get("DataBase", "db")
        self.sql_log = WriteLog(file_name="sql_log", log_name="sql", log_level="INFO")
        # self.__account = 'root'
        # self.__pwd = 'my123456'
        # self.__db = 'spider'

    def connect(self):
        # cursorclass = pymysql.cursors.DictCursor 参数定义返回结果为字典型
        self.db = pymysql.connect(host=self.__ip,
                                  user=self.__account,
                                  password=self.__pwd,
                                  database=self.__db,
                                  cursorclass=pymysql.cursors.DictCursor)
        self.cursor = self.db.cursor()

    def __search_execute(self, order: str):
        """
        order为查询命令，返回列表，列表内字典为sql查询结果。[{order:1},{order:2}]
        :param order_string:
        :return: list: [{order:1},{order:2}]
        """
        try:
            self.cursor.execute(order)  # 执行sql指令
            ret_list = self.cursor.fetchall()  # 命令返回，列表中包含多个字典条目
            if type(ret_list) != list:
                ret_list = []

        except Exception as e:
            self.sql_log.write_in("执行SQL查询指令出错，出错信息：\n{}".format(traceback.format_exc()), level="ERROR")# print("执行SQL查询指令出错，出错信息：" + str(e))
            raise Exception("执行SQL查询指令出错，出错信息：" + str(e))

        return ret_list

    def baidu_realtime_select(self, order_dic: dict, mode=None):
        # 字典仅用于注释，可随意修改内容
        mode_dic = {"mode_00": "默认指令，选取七天内的热搜",
                    "mode_01": "检查当前采集条目是否已存在于三天内的数据库中",
                    }
        if mode not in mode_dic.keys():  # 保证mode在keys中
            mode = "mode_00"
            self.sql_log.write_in("baidu_realtime_select输入为未知sql模式，重置为mode_00")

        mode_select = mode_dic.get(mode, mode_dic["mode_00"])
        self.connect()
        order = self.config.get("BD_RealTime_Select", mode).format(**order_dic)

        ret_list = self.__search_execute(order)

        return ret_list

    def baidu_realtime_insert(self, order_dic: dict, mode=None):
        # 字典仅用于注释，可随意修改内容
        mode_dic = {"mode_00": "默认指令，插入指定内容",
                    "mode_01": "采集时插入新采集的百度热搜信息",
                    "mode_02": "百度首页搜索各站点发布的热搜摘要"
                    }
        if mode not in mode_dic.keys():  # 保证mode在keys中
            mode = "mode_00"
            self.sql_log.write_in("baidu_realtime_insert输入为未知sql模式，重置为mode_00")

        # mode_select = mode_dic.get(mode, mode_dic["mode_00"])
        self.connect()
        order = self.config.get("BD_RealTime_Insert", mode).format(**order_dic)

        # print(order)
        try:
            self.cursor.execute(order)
            self.db.commit()  # 提交到数据库执行
        except:
            # 如果发生错误则回滚
            self.sql_log.write_in("指令执行错误：\n{}".format(order), level="ERROR")
            self.db.rollback()

    def baidu_content_select(self, order_dic: dict, mode=None):
        # 字典仅用于注释，可随意修改内容
        mode_dic = {"mode_00": "默认指令，查询所有正文为空的条目且采集时间为近7日的条目",
                    "mode_01": "查找过去1小时新增的数据条目，用于检测程序是否在运行",
                    }
        if mode not in mode_dic.keys():  # 保证mode在keys中
            mode = "mode_00"
            self.sql_log.write_in("baidu_content_select输入为未知sql模式，重置为mode_00")

        # mode_select = mode_dic.get(mode, mode_dic["mode_00"])
        self.connect()
        order = self.config.get("BD_Content_Select", mode).format(**order_dic)

        ret_list = self.__search_execute(order)

        return ret_list

    def baidu_content_insert(self, order_dic: dict, mode=None):
        # 字典仅用于注释，可随意修改内容
        mode_dic = {"mode_00": "百度首页搜索各站点发布的热搜摘要"
                    }
        if mode not in mode_dic.keys():  # 保证mode在keys中
            mode = "mode_00"
            self.sql_log.write_in("baidu_content_insert输入为未知sql模式，重置为mode_00")

        # mode_select = mode_dic.get(mode, mode_dic["mode_00"])
        self.connect()
        order = self.config.get("BD_Content_Insert", mode).format(**order_dic)

        try:
            self.cursor.execute(order)
            self.db.commit()  # 提交到数据库执行
        except:
            # 如果发生错误则回滚
            self.sql_log.write_in("指令执行错误：\n{}".format(order), level="ERROR")
            self.db.rollback()

    def baidu_content_update(self, order_dic: dict, mode=None):
        # 字典仅用于注释，可随意修改内容
        mode_dic = {"mode_00": "回填采集时间为当前时间",
                    "mode_01": "回填采集时间为当前时间, 回填智能提取出的标题正文等信息",
                    }
        if mode not in mode_dic.keys():  # 保证mode在keys中
            mode = "mode_00"
            self.sql_log.write_in("baidu_content_update输入为未知sql模式，重置为mode_00")
        # mode_select = mode_dic.get(mode, mode_dic["mode_00"])
        self.connect()
        order = self.config.get("BD_Content_Update", mode).format(**order_dic)
        try:
            self.cursor.execute(order)
            self.db.commit()  # 提交到数据库执行
        except:
            # 如果发生错误则回滚
            self.sql_log.write_in("指令执行错误：\n{}".format(order), level="ERROR")
            self.db.rollback()

    def baidu_recollect_insert(self, order_dic: dict, mode=None):
        # 字典仅用于注释，可随意修改内容
        mode_dic = {"mode_00": "插入暂时无法获取到咨询的百度热搜"
                    }
        if mode not in mode_dic.keys():  # 保证mode在keys中
            mode = "mode_00"
            self.sql_log.write_in("baidu_recollect_insert输入为未知sql模式，重置为mode_00")

        # mode_select = mode_dic.get(mode, mode_dic["mode_00"])
        self.connect()
        order = self.config.get("BD_ReCollect_Insert", mode).format(**order_dic)

        try:
            self.cursor.execute(order)
            self.db.commit()  # 提交到数据库执行
        except:
            # 如果发生错误则回滚
            self.sql_log.write_in("指令执行错误：\n{}".format(order), level="ERROR")
            self.db.rollback()

    def baidu_recollect_select(self, order_dic: dict, mode=None):
        # 字典仅用于注释，可随意修改内容
        mode_dic = {"mode_00": "查询7天内，半小时前的热搜条目",
                    "mode_01": "待定",
                    }
        if mode not in mode_dic.keys():  # 保证mode在keys中
            mode = "mode_00"
            self.sql_log.write_in("baidu_recollect_select输入为未知sql模式，重置为mode_00")

        # mode_select = mode_dic.get(mode, mode_dic["mode_00"])
        self.connect()
        order = self.config.get("BD_ReCollect_Select", mode).format(**order_dic)

        ret_list = self.__search_execute(order)

        return ret_list

    def baidu_recollect_update(self, order_dic: dict, mode=None):
        # 字典仅用于注释，可随意修改内容
        mode_dic = {"mode_00": "将指定条目的采集状态设置为True，也就是不再采集",
                    "mode_01": "待定",
                    }
        if mode not in mode_dic.keys():  # 保证mode在keys中
            mode = "mode_00"
            self.sql_log.write_in("baidu_recollect_update输入为未知sql模式，重置为mode_00")
        # mode_select = mode_dic.get(mode, mode_dic["mode_00"])
        self.connect()
        order = self.config.get("BD_ReCollect_Update", mode).format(**order_dic)
        try:
            self.cursor.execute(order)
            self.db.commit()  # 提交到数据库执行
        except:
            # 如果发生错误则回滚
            self.sql_log.write_in("指令执行错误：\n{}".format(order), level="ERROR")
            self.db.rollback()

    def neteast_content_insert(self, order_dic: dict, mode=None):
        # 字典仅用于注释，可随意修改内容
        mode_dic = {"mode_00": "插入网易热点要闻数据"
                    }
        if mode not in mode_dic.keys():  # 保证mode在keys中
            mode = "mode_00"
            self.sql_log.write_in("neteast_content_insert输入为未知sql模式，重置为mode_00")

        # mode_select = mode_dic.get(mode, mode_dic["mode_00"])
        self.connect()
        order = self.config.get("NE_Content_Insert", mode).format(**order_dic)

        try:
            self.cursor.execute(order)
            self.db.commit()  # 提交到数据库执行
        except:
            # 如果发生错误则回滚
            self.sql_log.write_in("指令执行错误：\n{}".format(order), level="ERROR")
            self.db.rollback()

    def neteast_content_select(self, order_dic: dict, mode=None):
        # 字典仅用于注释，可随意修改内容
        mode_dic = {"mode_00": "查询14天内，相同的url网易热点要闻",
                    "mode_01": "查找过去1小时新增的数据条目，用于检测程序是否在运行",
                    }
        if mode not in mode_dic.keys():  # 保证mode在keys中
            mode = "mode_00"
            self.sql_log.write_in("neteast_content_select输入为未知sql模式，重置为mode_00")

        # mode_select = mode_dic.get(mode, mode_dic["mode_00"])
        self.connect()
        order = self.config.get("NE_Content_Select", mode).format(**order_dic)

        ret_list = self.__search_execute(order)

        return ret_list

    def toutiao_content_select(self, order_dic: dict, mode=None):
        # 字典仅用于注释，可随意修改内容
        mode_dic = {"mode_00": "查询14天内，相同的url头条热点要闻",
                    "mode_01": "查找过去1小时新增的数据条目，用于检测程序是否在运行",}
        if mode not in mode_dic.keys():  # 保证mode在keys中
            mode = "mode_00"
            self.sql_log.write_in("toutiao_content_select输入为未知sql模式，重置为mode_00")

        # mode_select = mode_dic.get(mode, mode_dic["mode_00"])
        self.connect()
        order = self.config.get("TT_Content_Select", mode).format(**order_dic)

        ret_list = self.__search_execute(order)

        return ret_list

    def toutiao_content_insert(self, order_dic: dict, mode=None):
        # 字典仅用于注释，可随意修改内容
        mode_dic = {"mode_00": "插入头条热点要闻数据"
                    }
        if mode not in mode_dic.keys():  # 保证mode在keys中
            mode = "mode_00"
            self.sql_log.write_in("toutiao_content_insert输入为未知sql模式，重置为mode_00")

        # mode_select = mode_dic.get(mode, mode_dic["mode_00"])
        self.connect()
        order = self.config.get("TT_Content_Insert", mode).format(**order_dic)

        try:
            self.cursor.execute(order)
            self.db.commit()  # 提交到数据库执行
        except:
            # 如果发生错误则回滚
            self.sql_log.write_in("指令执行错误：\n{}".format(order), level="ERROR")
            self.db.rollback()


if __name__ == "__main__":
    import os
    work_dir = ""
    sqlserver = SqlServe(work_dir=work_dir)
    ret_list = sqlserver.baidu_recollect_select({})
    print(ret_list)




