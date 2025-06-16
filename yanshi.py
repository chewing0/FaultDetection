# 安装必要库（首次运行需要安装）
# pip install sentence-transformers scikit-learn

from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
import numpy as np
import torch

# 加载中文预训练模型
model = SentenceTransformer(
    'all-MiniLM-L6-v2',
    device='cuda' if torch.cuda.is_available() else 'cpu',
    cache_folder=r"D:\wby\projectfiles\XW\code\txt2vec\hugface-model\allenai-specter"
)

# 示例数据
words = ["猫", "小猫", "布偶猫", "狗", "小狗", "金毛", "波斯猫", "柯基"]

# 生成语义嵌入向量
embeddings = model.encode(words)

# 使用K-means聚类
num_clusters = 2  # 根据语义类别数量调整
kmeans = KMeans(n_clusters=num_clusters, random_state=0)
clusters = kmeans.fit_predict(embeddings)

# 组织聚类结果
clustered_words = {}
for word, cluster_id in zip(words, clusters):
    if cluster_id not in clustered_words:
        clustered_words[cluster_id] = []
    clustered_words[cluster_id].append(word)

# 打印聚类结果
for cluster_id, items in clustered_words.items():
    print(f"Cluster {cluster_id}: {', '.join(items)}")
