from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import tkinter as tk
from tkinter import filedialog
import torch
import os
import time

start_time = time.time()

root = tk.Tk()
root.withdraw() # 隐藏主窗口
f_path = filedialog.askopenfilename(title="选择日志文件", filetypes=[("Text files", "*.txt")])
print(f"选择的文件: {f_path}")

# 读取文本文件
with open(f_path, 'r', encoding='utf-8') as f:
    text = f.read().split()

# 加载预训练模型
model = SentenceTransformer(
    'all-MiniLM-L6-v2',
    # 'all-mpnet-base-v2',
    device='cuda' if torch.cuda.is_available() else 'cpu',
    cache_folder=r"D:\wby\projectfiles\XW\code\txt2vec\hugface-model"
)

# 生成向量表示
vector = model.encode([text], convert_to_numpy=True)

print("向量形状:", vector.shape)

end_time = time.time()
print("耗时: {:.2f}秒".format(end_time - start_time))