from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import tkinter as tk
from tkinter import filedialog
import sys

def text_deal():
    root = tk.Tk()
    root.withdraw() # 隐藏主窗口
    f_path = filedialog.askopenfilename(title="选择日志文件", filetypes=[("Text files", "*.txt")])
    print(f"选择的文件: {f_path}")

    # 读取文本文件
    with open(f_path, 'r', encoding='utf-8') as f:
        text = f.readlines()
        out = []
        for i in range(len(text)-1):
            text1 = text[i].split()
            text2 = text[i+1].split()
            if text1[-1] != text2[-1]:
                out += text1
    out += text[-1].split()
    return out

def open_file(title='选择您需要的文件'):
    root = tk.Tk()
    root.withdraw() # 隐藏主窗口
    f_path = filedialog.askopenfilename(title=title, filetypes=[("Text files", "*.txt")])
    print(f"选择的文件: {f_path}")
    # 读取文本文件
    with open(f_path, 'r', encoding='utf-8') as f:
        text = f.readlines()
    return text


# def text_deal2(text):
#     # 日志文本清晰，针对9005日志文本
#     out = []
#     for i in range(len(text)-1):
#         text1 = text[i].split()
#         text2 = text[i+1].split()
#         if text1[-1] != 'systemInformationBlockType':
#             out.append(text1)
#     out.append(text[-1].split())
#     outtext = []
#     for i in range(len(out)-1):
#         text1 = out[i]
#         text2 = out[i+1]
#         if text1[-1] != text2[-1]:
#             outtext += text1[10:]
#     outtext += out[-1][10:]
#     outtext = ' '.join(outtext)
#     return outtext

def text_deal2(text):
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