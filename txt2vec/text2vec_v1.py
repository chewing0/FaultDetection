"""
日志异常检测系统 v1.0
改进版本，提供更好的代码结构、错误处理和用户体验
"""

import os
import csv
import re
import sys
import time
import logging
from typing import List, Tuple, Optional, Union
from pathlib import Path

import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class Config:
    """配置类，统一管理系统配置"""
    
    # 模型路径
    MODEL_PATH = r'XW\FaultDetection\txt2vec\hugface-model\models--sentence-transformers--all-MiniLM-L6-v2\snapshots\c9745ed1d9f207416be6d2e6f8de32d1f16199bf'
    
    # 数据库路径
    DATABASE_PATH = r'XW\FaultDetection\txt2vec\error_database\database.csv'
    
    # 异常检测阈值
    ANOMALY_THRESHOLD = 0.8
    
    # 日志配置
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


class LogProcessor:
    """日志处理器，负责日志文件的读取和预处理"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def select_file(self, title: str = '选择您需要的文件', file_types: List[Tuple[str, str]] = None) -> Optional[str]:
        """
        文件选择对话框
        
        Args:
            title: 对话框标题
            file_types: 文件类型过滤器
            
        Returns:
            选择的文件路径，如果取消则返回None
        """
        if file_types is None:
            file_types = [("Text files", "*.txt"), ("All files", "*.*")]
        
        try:
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口
            file_path = filedialog.askopenfilename(title=title, filetypes=file_types)
            
            if not file_path:
                self.logger.info("用户取消了文件选择")
                return None
                
            self.logger.info(f"选择的文件: {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"文件选择失败: {e}")
            messagebox.showerror("错误", f"文件选择失败: {e}")
            return None
    
    def read_log_file(self, file_path: str) -> Optional[List[str]]:
        """
        读取日志文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容行列表，失败返回None
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            self.logger.info(f"成功读取文件，共 {len(lines)} 行")
            return lines
            
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    lines = f.readlines()
                self.logger.info(f"使用GBK编码成功读取文件，共 {len(lines)} 行")
                return lines
            except Exception as e:
                self.logger.error(f"读取文件失败 (编码问题): {e}")
                messagebox.showerror("错误", f"文件编码不支持: {e}")
                return None
        except Exception as e:
            self.logger.error(f"读取文件失败: {e}")
            messagebox.showerror("错误", f"读取文件失败: {e}")
            return None
    
    def clean_log_text(self, text_lines: List[str]) -> Optional[str]:
        """
        清洗日志文本（针对9005日志格式）
        
        Args:
            text_lines: 原始日志行列表
            
        Returns:
            清洗后的文本字符串，失败返回None
        """
        try:
            if not text_lines:
                raise ValueError("输入的日志文本为空")
            
            # 第一步：过滤掉包含 'systemInformationBlockType' 的行
            filtered_lines = []
            for i in range(len(text_lines) - 1):
                line1_parts = text_lines[i].split()
                line2_parts = text_lines[i + 1].split()
                
                if line1_parts and line1_parts[-1] != 'systemInformationBlockType':
                    filtered_lines.append(line1_parts)
            
            # 添加最后一行
            if text_lines:
                filtered_lines.append(text_lines[-1].split())
            
            # 第二步：提取有效内容（从第11个字段开始）
            processed_text = []
            for i in range(len(filtered_lines) - 1):
                line1 = filtered_lines[i]
                line2 = filtered_lines[i + 1]
                
                # 检查最后一个字段是否不同
                if line1 and line2 and len(line1) > 10 and len(line2) > 10:
                    if line1[-1] != line2[-1]:
                        processed_text.extend(line1[10:])
            
            # 添加最后一行的内容
            if filtered_lines and len(filtered_lines[-1]) > 10:
                processed_text.extend(filtered_lines[-1][10:])
            
            result = ' '.join(processed_text)
            
            if not result.strip():
                raise ValueError("处理后的文本为空，可能不是有效的9005日志格式")
            
            self.logger.info(f"日志清洗完成，输出长度: {len(result)}")
            return result
            
        except Exception as e:
            self.logger.error(f"日志清洗失败: {e}")
            messagebox.showerror("错误", f"日志清洗失败，可能不是9005日志格式: {e}")
            return None


class VectorEngine:
    """向量化引擎，负责文本向量化和相似度计算"""
    
    def __init__(self, model_path: str = Config.MODEL_PATH):
        """
        初始化向量化引擎
        
        Args:
            model_path: 模型路径
        """
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.model_path = model_path
        self._load_model()
    
    def _load_model(self) -> None:
        """加载Sentence Transformer模型"""
        try:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"模型路径不存在: {self.model_path}")
            
            self.logger.info("正在加载模型...")
            self.model = SentenceTransformer(self.model_path)
            self.logger.info("模型加载成功")
            
        except Exception as e:
            self.logger.error(f"模型加载失败: {e}")
            messagebox.showerror("错误", f"模型加载失败: {e}")
            sys.exit(1)
    
    def text_to_vector(self, text: str) -> Optional[np.ndarray]:
        """
        将文本转换为向量
        
        Args:
            text: 输入文本
            
        Returns:
            文本向量，失败返回None
        """
        try:
            if not text.strip():
                raise ValueError("输入文本为空")
            
            if self.model is None:
                raise RuntimeError("模型未正确加载")
            
            vector = self.model.encode([text], convert_to_numpy=True)[0]
            self.logger.debug(f"文本向量化完成，维度: {vector.shape}")
            return vector
            
        except Exception as e:
            self.logger.error(f"文本向量化失败: {e}")
            messagebox.showerror("错误", f"文本向量化失败: {e}")
            return None
    
    def calculate_similarity(self, vector1: np.ndarray, vector2: np.ndarray) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            vector1: 向量1
            vector2: 向量2
            
        Returns:
            余弦相似度值
        """
        try:
            similarity = cosine_similarity(
                vector1.reshape(1, -1), 
                vector2.reshape(1, -1)
            )[0][0]
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"相似度计算失败: {e}")
            return 0.0


class FaultDatabase:
    """故障数据库管理器"""
    
    def __init__(self, database_path: str = Config.DATABASE_PATH):
        """
        初始化故障数据库
        
        Args:
            database_path: 数据库文件路径
        """
        self.logger = logging.getLogger(__name__)
        self.database_path = database_path
        self._ensure_database_exists()
    
    def _ensure_database_exists(self) -> None:
        """确保数据库文件存在"""
        try:
            database_dir = os.path.dirname(self.database_path)
            if database_dir and not os.path.exists(database_dir):
                os.makedirs(database_dir, exist_ok=True)
                self.logger.info(f"创建数据库目录: {database_dir}")
            
            if not os.path.exists(self.database_path):
                # 创建空的CSV文件
                with open(self.database_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(['vector', 'error_type'])  # 写入标题行
                self.logger.info(f"创建新的数据库文件: {self.database_path}")
                
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
            messagebox.showerror("错误", f"数据库初始化失败: {e}")
    
    def add_fault_record(self, vector: np.ndarray, error_type: str) -> bool:
        """
        添加故障记录到数据库
        
        Args:
            vector: 故障向量
            error_type: 故障类型
            
        Returns:
            是否添加成功
        """
        try:
            with open(self.database_path, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                # 将向量转换为字符串格式
                vector_str = ' '.join(map(str, vector))
                writer.writerow([vector_str, error_type])
            
            self.logger.info(f"成功添加故障记录: {error_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加故障记录失败: {e}")
            messagebox.showerror("错误", f"添加故障记录失败: {e}")
            return False
    
    def load_fault_records(self) -> Tuple[List[np.ndarray], List[str]]:
        """
        从数据库加载所有故障记录
        
        Returns:
            (向量列表, 错误类型列表)
        """
        vectors = []
        error_types = []
        
        try:
            if not os.path.exists(self.database_path):
                self.logger.warning("数据库文件不存在")
                return vectors, error_types
            
            df = pd.read_csv(self.database_path, header=None)
            
            for i in range(len(df)):
                # 跳过标题行
                if i == 0 and df.iloc[i, 1] == 'error_type':
                    continue
                
                vector_string = str(df.iloc[i, 0])
                error_type = str(df.iloc[i, 1])
                
                # 解析向量字符串
                try:
                    cleaned_text = vector_string.strip('"\' []')
                    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
                    values = cleaned_text.split()
                    vector = np.array([float(val) for val in values])
                    
                    vectors.append(vector)
                    error_types.append(error_type)
                    
                except ValueError as ve:
                    self.logger.warning(f"跳过无效的向量记录 (行 {i}): {ve}")
                    continue
            
            self.logger.info(f"成功加载 {len(vectors)} 条故障记录")
            return vectors, error_types
            
        except Exception as e:
            self.logger.error(f"加载故障记录失败: {e}")
            messagebox.showerror("错误", f"加载故障记录失败: {e}")
            return [], []


class AnomalyDetector:
    """异常检测器，整合所有功能模块"""
    
    def __init__(self):
        """初始化异常检测器"""
        self.logger = logging.getLogger(__name__)
        self.log_processor = LogProcessor()
        self.vector_engine = VectorEngine()
        self.fault_database = FaultDatabase()
    
    def detect_anomaly_by_comparison(self) -> None:
        """通过与正常日志对比进行异常检测"""
        try:
            print("\n" + "="*50)
            print("异常检测 - 与正常日志对比")
            print("="*50)
            
            # 选择正常日志文件
            normal_file = self.log_processor.select_file('选择正常日志文件')
            if not normal_file:
                return
            
            # 选择待检测日志文件
            test_file = self.log_processor.select_file('选择待检测日志文件')
            if not test_file:
                return
            
            # 读取和处理正常日志
            normal_lines = self.log_processor.read_log_file(normal_file)
            if not normal_lines:
                return
            
            normal_text = self.log_processor.clean_log_text(normal_lines)
            if not normal_text:
                return
            
            # 读取和处理待检测日志
            test_lines = self.log_processor.read_log_file(test_file)
            if not test_lines:
                return
            
            test_text = self.log_processor.clean_log_text(test_lines)
            if not test_text:
                return
            
            # 向量化
            normal_vector = self.vector_engine.text_to_vector(normal_text)
            test_vector = self.vector_engine.text_to_vector(test_text)
            
            if normal_vector is None or test_vector is None:
                return
            
            # 计算相似度
            similarity = self.vector_engine.calculate_similarity(normal_vector, test_vector)
            
            # 显示结果
            print(f"\n余弦相似度: {similarity:.4f}")
            print(f"异常阈值: {Config.ANOMALY_THRESHOLD}")
            print("-" * 50)
            
            if similarity <= Config.ANOMALY_THRESHOLD:
                print("🚨 检测结果: 待检测文件可能存在异常！")
                print("建议进一步检查日志内容。")
            else:
                print("✅ 检测结果: 待检测文件正常")
                print("未发现明显异常。")
            
            print("="*50)
            
        except Exception as e:
            self.logger.error(f"异常检测失败: {e}")
            messagebox.showerror("错误", f"异常检测失败: {e}")
    
    def identify_fault_type(self) -> None:
        """通过故障库识别故障类型"""
        try:
            print("\n" + "="*50)
            print("故障类型识别")
            print("="*50)
            
            # 加载故障库
            vectors, error_types = self.fault_database.load_fault_records()
            
            if not vectors:
                print("❌ 故障库为空，请先添加故障记录。")
                return
            
            print(f"故障库中共有 {len(vectors)} 条记录")
            
            # 选择待检测文件
            test_file = self.log_processor.select_file('选择待检测日志文件')
            if not test_file:
                return
            
            # 读取和处理日志
            test_lines = self.log_processor.read_log_file(test_file)
            if not test_lines:
                return
            
            test_text = self.log_processor.clean_log_text(test_lines)
            if not test_text:
                return
            
            # 向量化
            test_vector = self.vector_engine.text_to_vector(test_text)
            if test_vector is None:
                return
            
            # 计算与故障库中每个记录的相似度
            similarities = []
            for fault_vector in vectors:
                similarity = self.vector_engine.calculate_similarity(test_vector, fault_vector)
                similarities.append(similarity)
            
            # 找到最相似的故障类型
            max_similarity_idx = np.argmax(similarities)
            predicted_fault = error_types[max_similarity_idx]
            max_similarity = similarities[max_similarity_idx]
            
            # 显示结果
            print(f"\n预测的故障类型: {predicted_fault}")
            print(f"最高相似度: {max_similarity:.4f}")
            
            # 显示前3个最相似的结果
            sorted_indices = np.argsort(similarities)[::-1]
            print("\n相似度排名前3的故障类型:")
            print("-" * 30)
            for i, idx in enumerate(sorted_indices[:3]):
                print(f"{i+1}. {error_types[idx]} (相似度: {similarities[idx]:.4f})")
            
            print("="*50)
            
        except Exception as e:
            self.logger.error(f"故障类型识别失败: {e}")
            messagebox.showerror("错误", f"故障类型识别失败: {e}")
    
    def add_fault_to_database(self) -> None:
        """添加新的故障记录到数据库"""
        try:
            print("\n" + "="*50)
            print("添加故障记录到数据库")
            print("="*50)
            
            # 选择故障日志文件
            fault_file = self.log_processor.select_file('选择故障日志文件')
            if not fault_file:
                return
            
            # 读取和处理故障日志
            fault_lines = self.log_processor.read_log_file(fault_file)
            if not fault_lines:
                return
            
            fault_text = self.log_processor.clean_log_text(fault_lines)
            if not fault_text:
                return
            
            # 向量化
            fault_vector = self.vector_engine.text_to_vector(fault_text)
            if fault_vector is None:
                return
            
            # 获取故障类型
            print("\n请输入故障类型名称:")
            print("建议使用简洁明确的描述，例如:")
            print("- 连接超时")
            print("- 内存溢出") 
            print("- 配置错误")
            print("- 网络异常")
            
            error_type = input("\n故障类型: ").strip()
            
            if not error_type:
                print("❌ 故障类型不能为空")
                return
            
            # 保存到数据库
            if self.fault_database.add_fault_record(fault_vector, error_type):
                print(f"✅ 成功添加故障记录: {error_type}")
            else:
                print("❌ 添加故障记录失败")
            
            print("="*50)
            
        except Exception as e:
            self.logger.error(f"添加故障记录失败: {e}")
            messagebox.showerror("错误", f"添加故障记录失败: {e}")


def setup_logging():
    """配置日志系统"""
    logging.basicConfig(
        level=Config.LOG_LEVEL,
        format=Config.LOG_FORMAT,
        handlers=[
            logging.FileHandler('anomaly_detection.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def show_menu() -> str:
    """显示主菜单"""
    print("\n" + "="*50)
    print("🔍 日志异常检测系统 v1.0")
    print("="*50)
    print("1. 异常检测 (与正常日志对比)")
    print("2. 故障类型识别 (与故障库对比)")
    print("3. 添加故障记录到数据库")
    print("4. 查看系统信息")
    print("0. 退出程序")
    print("="*50)
    return input("请选择功能 (0-4): ").strip()


def show_system_info():
    """显示系统信息"""
    print("\n" + "="*50)
    print("系统信息")
    print("="*50)
    print(f"模型路径: {Config.MODEL_PATH}")
    print(f"数据库路径: {Config.DATABASE_PATH}")
    print(f"异常检测阈值: {Config.ANOMALY_THRESHOLD}")
    
    # 检查文件是否存在
    model_exists = os.path.exists(Config.MODEL_PATH)
    db_exists = os.path.exists(Config.DATABASE_PATH)
    
    print(f"模型状态: {'✅ 存在' if model_exists else '❌ 不存在'}")
    print(f"数据库状态: {'✅ 存在' if db_exists else '❌ 不存在'}")
    
    if db_exists:
        try:
            df = pd.read_csv(Config.DATABASE_PATH)
            record_count = len(df) - 1 if len(df) > 0 else 0  # 减去标题行
            print(f"故障记录数量: {record_count}")
        except Exception:
            print("故障记录数量: 无法读取")
    
    print("="*50)


def main():
    """主函数"""
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🚀 正在初始化系统...")
    
    try:
        # 初始化检测器
        detector = AnomalyDetector()
        print("✅ 系统初始化完成")
        
        while True:
            choice = show_menu()
            start_time = time.time()
            
            if choice == '0':
                print("\n👋 感谢使用日志异常检测系统！再见！")
                break
            elif choice == '1':
                detector.detect_anomaly_by_comparison()
            elif choice == '2':
                detector.identify_fault_type()
            elif choice == '3':
                detector.add_fault_to_database()
            elif choice == '4':
                show_system_info()
            else:
                print("\n❌ 无效的选择，请重新输入！")
                continue
            
            end_time = time.time()
            print(f"\n⏱️  操作耗时: {end_time - start_time:.2f}秒")
            
            input("\n按回车键继续...")
    
    except KeyboardInterrupt:
        print("\n\n👋 用户中断程序，再见！")
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        print(f"\n❌ 程序运行出错: {e}")
        input("按回车键退出...")


if __name__ == "__main__":
    main()