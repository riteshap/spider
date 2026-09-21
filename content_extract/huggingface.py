
import numpy as np
from transformers import BertTokenizer, BertModel

# text = torch.tensor(["上山打老虎", "一二三"])
# input_ids2 = torch.tensor([[101, 677, 102]])
# input_ids = torch.tensor([[101, 677, 102, 0],
#                           [101, 677, 2255, 102]])
# attention_mask = torch.tensor([[1, 1, 1, 0],
#                                [1, 1, 1, 1]])  # 控制记录文本长度

tokenizer = BertTokenizer.from_pretrained(r'./bert-base-chinese')
model = BertModel.from_pretrained(r'./bert-base-chinese')
encoded_input = tokenizer("上山打老虎", return_tensors='pt')

text = ("上山打老虎", "一二三")
out = tokenizer.batch_encode_plus(["上山打老虎", "一二三"])
# output = model(input_ids=input_ids, attention_mask=attention_mask)
# seq_output = output[0]
# pooler_output = output[1]
print("over")




