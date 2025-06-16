from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import tkinter as tk
from tkinter import filedialog
import sys
import csv
import numpy as np
import pandas as pd
import re

database_path = r'XW\code\txt2vec\error_database\database.csv'
# 核心功能
# Anomaly_Detection：通过和正常值的对比进行异常检测
# vec_save：保存日志向量
# csv_reader：读取保存日志向量的文件
# ---------------------------------------
# open_file：传入参数为文件选择框提示，用于打开日志文件
# text_deal：传入文本，进行日志文本清洗
# vec_similar：计算两个日志向量相似度
# open_csvfile：选择csv文件路径

# 文件选择
# title：选择文件窗口提示
def open_file(title='选择您需要的文件'):
    root = tk.Tk()
    root.withdraw() # 隐藏主窗口
    f_path = filedialog.askopenfilename(title=title, filetypes=[("Text files", "*.txt")])
    print(f"选择的文件: {f_path}")
    # 读取文本文件
    with open(f_path, 'r', encoding='utf-8') as f:
        text = f.readlines()
    return text

# 日志文件清洗
# text：需要清洗的日志文本
def text_deal(text):
    # 日志文本清洗，针对9005日志文本
    try:
        out = []
        for i in range(len(text)-1):
            text1 = text[i].split()
            text2 = text[i+1].split()
            if text1[-1] != 'systemInformationBlockType':
                out.append(text1)
        out.append(text[-1].split())
        outtext = []
        for i in range(len(out)-1):
            text1 = out[i]
            text2 = out[i+1]
            if text1[-1] != text2[-1]:
                outtext += text1[10:]
        outtext += out[-1][10:]
        outtext = ' '.join(outtext)
    except:
        print('您选择的不是9005日志')
        sys.exit(1)
    return outtext

# 文本转向量
# text：需要转向量的文本
def get_vec(text):
    return model.encode([text], convert_to_numpy=True)

# 获取日志向量
def get_logvec():
    logtext = open_file('选择您需要分析的日志')
    logtext = text_deal(logtext)
    logvec = get_vec(logtext)
    return logvec

# 相似度计算
def vec_similar(vector1, vector2):
    similarity = cosine_similarity(vector1.reshape(1, -1), vector2.reshape(1, -1))[0][0]
    return similarity

# 根据正常日志进行的异常检测
def Anomaly_Detection():
    file1 = open_file('选择正常日志文件')
    file2 = open_file('选择待检测日志文件')
    text1 = text_deal(file1)
    text2 = text_deal(file2)
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

# 下面是一系列的故障数据库建立逻辑
# 首先是打开存放故障日志向量和对应类型的故障数据库，这里使用csv文件代替数据库
def open_csvfile():
    root = tk.Tk()
    root.withdraw() # 隐藏主窗口
    f_path = filedialog.askopenfilename(title='选择存放故障数据的故障数据库', filetypes=[("CSV files", "*.csv")])
    return f_path

# 将故障日志向量和对应故障类型存放在故障库中
def vec_save():
    # csv_filepath = open_csvfile()
    csv_filepath = database_path
    csv_file = open(csv_filepath, 'a', newline='', encoding='utf-8-sig')
    writer = csv.writer(csv_file)
    err_text = open_file(title='请选择需要在故障库的异常日志')
    err_text = text_deal(err_text)
    err_vec = get_vec(err_text)
    err_type = input('请输入错误类型：')
    writer.writerow([err_vec, err_type])
    csv_file.close()

# 读取CSV文件
def csv_reader():
    # csv_filepath = open_csvfile()
    csv_filepath = database_path
    # 读取CSV文件，不指定header以确保我们能获取到第一行
    vectors = []
    errors = []
    dfs = pd.read_csv(csv_filepath, header=None)
    for i in range(len(dfs)):
        vector_string = dfs.iloc[i, 0]
        # 清理字符串
        cleaned_text = vector_string.strip('"\' []')
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        # 将字符串分割成数字列表
        values = cleaned_text.split()
        # 将字符串转换为浮点数
        vector = np.array([float(val) for val in values])
        vectors.append(vector)
        errors.append(dfs.iloc[i, 1])
    return vectors, errors

# 下面是一些和返回故障类型相关的逻辑
# 返回相似度矩阵，针对故障数据库数据，返回故障数据库中的元素的相似度矩阵
def similar_matrix(vectors):
    similar = []
    for i in range(len(vectors)):
        similar_i = []
        for j in range(len(vectors)):
            if i == j:
                similar_i.append(0.0)
            else:
                similar_i.append(vec_similar(vectors[i], vectors[j]))
        similar.append(similar_i)
    return similar

# 计算当前日志和故障数据库中日志的相似度，返回最疑似的可能
def error_type(log_vec, vectors, errs):
    similar = []
    for i in range(len(vectors)):
        similar.append(vec_similar(log_vec, vectors[i]))
    idx = np.argmax(similar)
    return errs[idx]

# 模型加载
model = SentenceTransformer(r'XW\code\txt2vec\hugface-model\models--sentence-transformers--all-MiniLM-L6-v2\snapshots\c9745ed1d9f207416be6d2e6f8de32d1f16199bf')
# model = SentenceTransformer(r'XW\code\txt2vec\hugface-model\qwen')
