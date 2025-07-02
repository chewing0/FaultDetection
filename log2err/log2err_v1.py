import sys
import os
from datetime import datetime
import tkinter as tk
from tkinter import filedialog

# 添加logany.py所在的路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入logany模块
try:
    from logany import ProtocolAnalyzer, result_out
    from fault_mapping import get_fault_mapping
except ImportError:
    print("无法导入logany模块或fault_mapping模块，请确保相关文件在同一目录下")
    sys.exit(1)

class FaultDiagnosisSystem:
    def __init__(self):
        """初始化故障诊断系统"""
        self.analyzer = ProtocolAnalyzer()
        
        # 从外部文件加载故障映射规则
        self.fault_mapping = get_fault_mapping()
    
    def analyze_log_file(self, file_path):
        """分析日志文件并返回故障诊断结果"""
        try:
            # 使用logany模块解析日志
            logs = self.analyzer.parse_log(file_path)
            if not logs:
                return {
                    "success": False,
                    "error": "日志文件为空或格式不正确"
                }
            
            # 分析流程完整性
            self.analyzer.analyze_flow_completeness(logs)
            report = self.analyzer.generate_analysis_report()
            
            # 获取流程顺序
            flow_order = list(self.analyzer.flow_definitions.keys())
            
            # 找到第一个错误
            first_error = self.analyzer.print_first_error(report, flow_order)
            
            # 生成故障诊断结果
            diagnosis_result = self.generate_fault_diagnosis(first_error, report)
            
            return {
                "success": True,
                "diagnosis": diagnosis_result,
                "detailed_report": report,
                "analyzed_logs_count": len(logs)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"分析过程中发生错误: {str(e)}"
            }
    
    def generate_fault_diagnosis(self, first_error, detailed_report):
        """根据分析结果生成故障诊断"""
        if first_error.get("status") == "all_flows_completed":
            return {
                "fault_type": "正常",
                "fault_description": "所有流程正常完成，系统运行正常"
            }
        
        blocking_flow = first_error.get("blocking_flow")
        status = first_error.get("status")
        
        if blocking_flow and blocking_flow in self.fault_mapping:
            fault_mapping = self.fault_mapping[blocking_flow]
            
            if status in fault_mapping:
                fault_description = fault_mapping[status]
                
                # 生成详细的故障信息
                diagnosis = {
                    "fault_type": self.extract_fault_type(fault_description),
                    "fault_description": fault_description,
                    "blocking_flow": blocking_flow,
                    "status": status
                }
                
                # 添加详细状态信息
                if "status_details" in first_error:
                    diagnosis["details"] = first_error["status_details"]
                
                return diagnosis
        
        # 默认故障描述
        return {
            "fault_type": "未知故障",
            "fault_description": f"在 {blocking_flow} 流程中检测到异常状态: {status}",
            "blocking_flow": blocking_flow,
            "status": status
        }
    
    def extract_fault_type(self, fault_description):
        """从故障描述中提取故障类型"""
        if "启动失败" in fault_description:
            return "启动失败"
        elif "卡MSG" in fault_description:
            return "流程中断"
        elif "失败" in fault_description:
            return "功能失败"
        elif "超时" in fault_description:
            return "超时异常"
        elif "异常" in fault_description:
            return "系统异常"
        else:
            return "未知故障"

    def print_diagnosis_result(self, result):
        """打印诊断结果"""
        if not result["success"]:
            print(f"分析失败: {result['error']}")
            return
        
        diagnosis = result["diagnosis"]
        
        print("=" * 60)
        print("5G日志故障诊断结果")
        print("=" * 60)
        print()
        
        print(f"故障类型: {diagnosis['fault_type']}")
        print(f"故障描述: {diagnosis['fault_description']}")
        print()
        
        if 'blocking_flow' in diagnosis:
            print(f"阻塞流程: {diagnosis['blocking_flow']}")
            print(f"流程状态: {diagnosis['status']}")
            print()
        
        # 显示详细信息
        if 'details' in diagnosis:
            print("详细信息:")
            for key, value in diagnosis['details'].items():
                print(f"  {key}: {value}")
            print()
        
        # 显示统计信息
        print("-" * 40)
        print("分析统计信息:")
        print(f"  已分析日志条数: {result['analyzed_logs_count']}")
        
        report = result['detailed_report']['summary']
        print(f"  总流程数: {report['total_flows']}")
        print(f"  已完成流程: {report['completed']}")
        print(f"  进行中流程: {report['in_progress']}")
        print(f"  未开始流程: {report['not_started']}")
        print("=" * 60)

def select_log_file():
    """使用文件对话框选择日志文件"""
    # 创建隐藏的根窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 打开文件选择对话框
    file_path = filedialog.askopenfilename(
        title="选择日志文件",
        filetypes=[
            ("Text files", "*.txt"),
            ("Log files", "*.log"), 
            ("All files", "*.*")
        ]
    )
    
    # 销毁根窗口
    root.destroy()
    
    return file_path

def main():
    """主函数"""
    print("5G日志故障诊断系统 v1.0")
    print("-" * 40)
    
    # 获取日志文件路径
    if len(sys.argv) > 1:
        # 如果有命令行参数，直接使用
        file_path = sys.argv[1]
    else:
        # 使用文件选择对话框
        print("请选择日志文件...")
        file_path = select_log_file()
    
    if not file_path:
        print("错误: 未选择日志文件")
        return
    
    if not os.path.exists(file_path):
        print(f"错误: 文件 {file_path} 不存在")
        return
    
    print(f"正在分析日志文件: {file_path}")
    print("=" * 60)
    
    # 创建故障诊断系统实例并分析
    diagnosis_system = FaultDiagnosisSystem()
    result = diagnosis_system.analyze_log_file(file_path)
    
    # 打印诊断结果
    diagnosis_system.print_diagnosis_result(result)

if __name__ == "__main__":
    main()