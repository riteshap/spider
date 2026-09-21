import torch
import pickle
import random
from torch import nn
from transformers import BertModel
from transformers import BertTokenizer, BertModel

batch_size = 64

device = (
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)

print(f"Using {device} device")


# Define model
class NeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        hidden_size = 128
        bert_hidden_size = 768
        self.bert = BertModel.from_pretrained(r'.\bert-base-chinese')
        self.linear_01 = nn.Linear(bert_hidden_size, hidden_size)
        self.linear_02 = nn.Linear(bert_hidden_size, hidden_size)

        self.bili = torch.nn.Bilinear(hidden_size, hidden_size, 2)

    def forward(self, title_idxs, title_masks, content_idxs, content_masks):
        title = self.bert(title_idxs, attention_mask=title_masks)[1]  # pooler_output
        content = self.bert(content_idxs, attention_mask=content_masks)[1]  # pooler_output
        title_liner = self.linear_01(title)
        content_liner = self.linear_02(content)

        output = self.bili(title_liner, content_liner)
        return output


class data_train:
    def __init__(self, batch_size, epoch, max_len):
        self.tensor_all_data = pickle.load(open("./tensor_all_data", "rb"))
        self.batch_size = batch_size
        self.epoch = epoch
        self.max_len = max_len
        self.epoch_num = 0
        self.index = 0
        random.shuffle(self.tensor_all_data)

    def generate(self):
        title_idxs = torch.zeros(size=(self.batch_size, self.max_len), dtype=torch.int64)
        content_idxs = torch.zeros(size=(self.batch_size, self.max_len), dtype=torch.int64)
        title_masks = torch.zeros(size=(self.batch_size, self.max_len), dtype=torch.int64)
        content_masks = torch.zeros(size=(self.batch_size, self.max_len), dtype=torch.int64)
        label = torch.zeros(size=(self.batch_size, ), dtype=torch.int64)
        if self.index + batch_size >= len(self.tensor_all_data):
            self.index = 0
            self.epoch_num += 1

        for i in range(self.batch_size):
            title_idxs[i] = self.tensor_all_data[i]["input_ids"][0]
            title_masks[i] = self.tensor_all_data[i]["input_masks"][0]
            content_idxs[i] = self.tensor_all_data[i]["input_ids"][1]
            content_masks[i] = self.tensor_all_data[i]["input_masks"][1]
            label[i] = self.tensor_all_data[i]["label"]

        self.index += batch_size

        return title_idxs, title_masks, content_idxs, content_masks, label


class config:
    """用于执行训练"""
    def __init__(self):
        self.model = NeuralNetwork().to(device)
        self.epoch = 50
        self.batch_size = 64
        self.max_len = 128
        self.data_train = data_train(self.batch_size, self.epoch, self.max_len)
        self.tokenizer = BertTokenizer.from_pretrained(r'./bert-base-chinese')
        print(self.model)  # pytorch直接打印即可查看模型结构

    def train(self):
        """执行模型训练"""
        self.model.train()
        while self.data_train.epoch_num < self.epoch:
            title_idxs, title_masks, content_idxs, content_masks, label = self.data_train.generate()

            loss_fn = nn.CrossEntropyLoss()  # torch的CrossEntropyLoss似乎自带对模型输出pred的softmax
            optimizer = torch.optim.SGD(self.model.parameters(), lr=1e-3)
            # Compute prediction error
            pred = self.model(title_idxs, title_masks, content_idxs, content_masks)
            loss = loss_fn(pred, label)

            # Backpropagation
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()

        torch.save(self.model.state_dict(), "model.pth")


if __name__ == "__main__":
    # dt = data_train(batch_size=64, epoch=5, max_len=128)
    # dt.generate()
    cif = config()
    cif.train()