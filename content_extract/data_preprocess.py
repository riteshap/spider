import pickle
import pandas as pd
import torch
import pickle

"""预处理训练数据，整合为数据类，用于训练，采用pytorch模型"""
class data_pre:
    def __init__(self):
        pass
    def fun_01(self):
        out_data_t = pd.read_excel("./out_data_t.xlsx")
        out_data_f = pd.read_excel("./out_data_f.xlsx")

        len_t = out_data_t.shape[1]
        len_f = out_data_f.shape[1]
        tt = out_data_t.head()
        data = []
        for i in range(len_t):
            try:
                title = out_data_t.loc[0, i]
                contents = []
                for ss in out_data_t.loc[1:, i]:
                    if str(ss) != "nan":
                        contents.append(ss)
                for content in contents:
                    data.append((title, content, 0))
            except Exception as e:
                continue


        for i in range(len_f):
            try:
                title = out_data_f.loc[0, i]
                contents = []
                for ss in out_data_t.loc[1:, i]:
                    if str(ss) != "nan":
                        contents.append(ss)
                for content in contents:
                    data.append((title, content, 1))
            except Exception as e:
                continue

        pickle.dump(data, open("all_data", "wb"))

        print("over")

    def fun_02(self):
        from transformers import BertTokenizer

        max_seq_len = 128
        tokenizer = BertTokenizer.from_pretrained(r'./bert-base-chinese')
        all_data = pickle.load(open("./all_data", "rb"))

        # 处理长度超过128的段落，标题不会超长度
        n_all_data = []
        for index, data in enumerate(all_data):
            if len(data[0]) > 126:  # 标题超长，说明原始数据有误
                continue
            if len(data[1]) <= 126:
                n_all_data.append(data)
                continue

            p_data = data[1].split("。")
            for a in p_data:
                if len(a) < 2:
                    continue
                n_all_data.append((data[0], a[:126], data[2]))  # 分句后仍然超长度就直接截断

        tensor_all_data = []
        for index, data in enumerate(n_all_data):
            # 将段落中词汇转换为id存储
            label = data[2]
            out = tokenizer.batch_encode_plus(data[:2])
            input_ids = torch.zeros(size=(2, max_seq_len), dtype=torch.int64)
            input_masks = torch.zeros(size=(2, max_seq_len), dtype=torch.int64)
            a = out.data["input_ids"]
            b = out.data["attention_mask"]
            for i in range(2):
                input_ids[i, :len(a[i])] = torch.tensor(a[i], dtype=torch.int64)
                input_masks[i, :len(b[i])] = torch.tensor(b[i], dtype=torch.int64)

            tensor_all_data.append({"input_ids": input_ids,
                                    "input_masks": input_masks,
                                    "label": label})

        pickle.dump(tensor_all_data, open("tensor_all_data", "wb"))

    def fun_03_test(self):
        from transformers import BertModel
        # 测试tensor_all_data中编号能否被bert处理
        tensor_all_data = pickle.load(open("./tensor_all_data", "rb"))
        model = BertModel.from_pretrained(r'./bert-base-chinese')
        input_ids = tensor_all_data[0]["input_ids"]
        attention_mask = tensor_all_data[0]["input_masks"]
        input_ids = torch.tensor(input_ids.numpy(), dtype=torch.int64)
        attention_mask = torch.tensor(attention_mask.numpy(), dtype=torch.int64)
        output = model(input_ids=input_ids, attention_mask=attention_mask)
        print("over")


if __name__ == "__main__":
    pr = data_pre()
    pr.fun_02()
