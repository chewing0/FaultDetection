from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import tkinter as tk
from tkinter import filedialog
import torch
import os

def get_file_vector(file_path):
    """读取文件并生成向量"""
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read().split()
    return model.encode([text], convert_to_numpy=True)

# 初始化GUI
root = tk.Tk()
root.withdraw()

# 选择第一个文件
print("请选择第一个文件")
file1 = filedialog.askopenfilename(
    title="选择第一个文件",
    filetypes=[("Text files", "*.txt")]
)
if not file1:
    print("未选择文件，程序退出")
    exit()
print(f"选择的文件: {file1}")

# 选择第二个文件
print("请选择第二个文件")
file2 = filedialog.askopenfilename(
    title="选择第二个文件",
    filetypes=[("Text files", "*.txt")]
)
if not file2:
    print("未选择文件，程序退出")
    exit()
print(f"选择的文件: {file2}")


# 加载模型（放在文件选择之后以避免不必要的加载）
model = SentenceTransformer(
    'all-MiniLM-L6-v2',
    device='cuda' if torch.cuda.is_available() else 'cpu',
    cache_folder=r"D:\wby\projectfiles\XW\code\txt2vec\hugface-model"
)

# model = SentenceTransformer(
#     'all-mpnet-base-v2',
#     device='cuda' if torch.cuda.is_available() else 'cpu',
#     cache_folder=r"D:\wby\projectfiles\XW\code\txt2vec\hugface-model\allenai-specter"
# )

# 生成向量
vec1 = get_file_vector(file1)
vec2 = get_file_vector(file2)

# 计算相似度
similarity = cosine_similarity(vec1, vec2)[0][0]

# 打印结果
print("\n" + "="*40)
print(f"文件1: {file1}")
print(f"文件2: {file2}")
print("-"*40)
print(f"向量维度: {vec1.shape[1]} 维")
print(f"余弦相似度: {similarity:.4f}")
print("="*40)

# 相似度解读
print("\n相似度解读：")
print("1.0 表示完全相同")
print("0.8~1.0 表示高度相似")
print("0.6~0.8 表示中等相似")
print("<0.6 表示差异较大")
