from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import time
from text2vec_textdeal import text_deal, text_deal2, open_file

# 模型加载
model = SentenceTransformer(r'XW\code\txt2vec\hugface-model\models--sentence-transformers--all-MiniLM-L6-v2\snapshots\c9745ed1d9f207416be6d2e6f8de32d1f16199bf')

def get_vec(text):
    return model.encode([text], convert_to_numpy=True)

def vec_similar():
    file1 = open_file('选择第一个文件')
    file2 = open_file('选择第二个文件')
    text1 = text_deal2(file1)
    text2 = text_deal2(file2)
    # 生成向量表示
    vector1 = get_vec(text1)
    vector2 = get_vec(text2)

    similarity = cosine_similarity(vector1, vector2)[0][0]

    # 打印结果
    print("\n" + "="*40)
    print(f"余弦相似度: {similarity:.4f}")
    print("="*40)

def Anomaly_Detection():
    file1 = open_file('选择正常日志文件')
    file2 = open_file('选择待检测日志文件')
    text1 = text_deal2(file1)
    text2 = text_deal2(file2)
    # 生成向量表示
    vector1 = get_vec(text1)
    vector2 = get_vec(text2)

    similarity = cosine_similarity(vector1, vector2)[0][0]

    print("\n" + "="*40)
    print(f"余弦相似度: {similarity:.4f}")
    print("="*40)
    if similarity <= 0.8:
        print("\n" + "="*40)
        print('！！！待检测文件可能存在异常！！！')
        print("="*40)
    else:
        print("\n" + "="*40)
        print('---待检测文件不存在异常---')
        print("="*40)


# vec_similar()
# Anomaly_Detection()
