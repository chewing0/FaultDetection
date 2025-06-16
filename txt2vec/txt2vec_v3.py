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

# 选择四个文件
files = []
for i in range(4):
    print(f"请选择第{i+1}个文件")
    file = filedialog.askopenfilename(
        title=f"选择第{i+1}个文件",
        filetypes=[("Text files", "*.txt")]
    )
    if not file:
        print("未选择文件，程序退出")
        exit()
    print(f"选择的文件: {file}")
    files.append(file)

for idx, path in enumerate(files, 1):
    print(f"[文件{idx}] {os.path.basename(path)}")

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

# 生成所有文件的向量
vectors = [get_file_vector(file) for file in files]

# 计算每个文件与其它文件的相似度
similarity_matrix = []
for i in range(4):
    row = []
    for j in range(4):
        if i == j:
            row.append(1.0)  # 与自身的相似度为1
        else:
            row.append(cosine_similarity(vectors[i], vectors[j])[0][0])
    similarity_matrix.append(row)

# 计算平均相似度（排除自身）
avg_similarities = [
    (sum(similarity_matrix[i]) - 1) / 3  # 减去自身相似度1.0后求平均
    for i in range(4)
]

# 找到最异常的文件
min_similarity = min(avg_similarities)
anomaly_index = avg_similarities.index(min_similarity)
anomaly_file = files[anomaly_index]

# 打印结果
print("\n" + "="*60)
print("各文件分析结果：")
for idx, (path, score) in enumerate(zip(files, avg_similarities)):
    status = "★异常文件★" if idx == anomaly_index else "正常文件"
    print(f"\n[{status}]")
    print(f"文件{idx+1}: {os.path.basename(path)}")
    print(f"平均相似度: {score:.4f}")

print("\n" + "="*60)
print(f"结论：文件【{os.path.basename(anomaly_file)}】与其他文件差异最大")
print(f"异常文件路径: {anomaly_file}")
print("="*60)

# 相似度解读
print("\n相似度解读：")
print("1.0 表示完全相同")
print("0.8~1.0 表示高度相似")
print("0.6~0.8 表示中等相似")
print("<0.6 表示差异较大")
