from datetime import datetime
from collections import deque
import json

class ProtocolAnalyzer:
    def __init__(self):
        # 扩展流程模板（包含关键5G流程）
        self.flow_definitions = {
            # 注册请求
            "Registration Request": {
                "steps" : [
                    {"msg": "Registration request", "protocol": "nas", "dir": "u"},
                ],
                "prerequisites": []
            },
            # RRC连接建立
            "RRC Connection Setup": {
                "steps" : [
                    {"msg": "rrcSetupRequest", "protocol": "nrrrc", "dir": "u"},
                    {"msg": "rrcSetup", "protocol": "nrrrc", "dir": "d"},
                    {"msg": "rrcSetupComplete", "protocol": "nrrrc", "dir": "u"},
                ],
                "prerequisites": ["Registration Request"]
            },
            # NAS身份认证
            "NAS Identity": {
                "steps" : [
                    {"msg": "Identity request", "protocol": "nas", "dir": "d"},
                    {"msg": "Identity response", "protocol": "nas", "dir": "u"},
                ],
                "prerequisites": ["Registration Request"]
            },
            # NAS鉴权
            "NAS Authentication": {
                "steps" : [
                    {"msg": "Authentication request", "protocol": "nas", "dir": "d"},
                    {"msg": "Authentication response", "protocol": "nas", "dir": "u"},
                ],
                "prerequisites": ["Registration Request"]
            },
            # RRC鉴权 注意这里后面需要修改额外校验NRRRC
            "RRC Authentication": {
                "steps" : [
                    {"msg": "Authentication request", "protocol": "nrrrc", "dir": "d"},
                    {"msg": "Authentication response", "protocol": "nrrrc", "dir": "u"},
                ],
                "prerequisites": ["Registration Request"]
            },
            # NAS SMC
            "NAS SMC": {
                "steps" : [
                    {"msg": "Security mode command", "protocol": "nas", "dir": "d"},
                    {"msg": "Security mode complete", "protocol": "nas", "dir": "u"},
                ],
                "prerequisites": ["NAS Authentication"]
            },
            # UE能力上报
            "UE Capability": {
                "steps" : [
                    {"msg": "ueCapabilityEnquiry", "protocol": "nrrrc", "dir": "d"},
                    {"msg": "ueCapabilityInformation", "protocol": "nrrrc", "dir": "u"},

                ],
                "prerequisites": ["NAS SMC"]
            },
            # RRC SMC
            "RRC SMC": {
                "steps" : [
                    {"msg": "securityModeCommand", "protocol": "nrrrc", "dir": "d"},
                    {"msg": "securityModeComplete", "protocol": "nrrrc", "dir": "u"},
                ],
                "prerequisites": ["RRC Authentication"]
            },
            # RRC重构
            "RRC Reconfig": {
                "steps" : [
                    {"msg": "rrcReconfiguration", "protocol": "nrrrc", "dir": "d"},
                    {"msg": "rrcReconfigurationComplete", "protocol": "nrrrc", "dir": "u"},
                ],
                "prerequisites": ["RRC SMC"]
            },
            # 注册成功
            "Registration response": {
                "steps" : [
                    {"msg": "Registration accept", "protocol": "nas", "dir": "d"},
                    {"msg": "Registration complete", "protocol": "nas", "dir": "u"},
                ],
                # 需要请求和前置都完成
                "prerequisites": ["UE Capability", "RRC Reconfig"]
            },
            # PDU建立
            "PDU session": {
                "steps" : [
                    {"msg": "PDU session establishment request", "protocol": "nas", "dir": "u"},
                    {"msg": "UL NAS transport", "protocol": "nas", "dir": "u"},
                    {"msg": "rrcReconfiguration", "protocol": "nrrrc", "dir": "d"},
                    {"msg": "rrcReconfigurationComplete", "protocol": "nrrrc", "dir": "u"},
                    {"msg": "DL NAS transport", "protocol": "nas", "dir": "d"},
                    {"msg": "PDU session establishment accept", "protocol": "nas", "dir": "d"},
                ],
                "prerequisites": ["Registration response"]
            },
            "SIP Registration": {
                "steps" : [
                    {"msg": "REGISTER", "protocol": "sip", "dir": "u"},
                    {"msg": "200 OK[REGISTER]", "protocol": "sip", "dir": "d"},
                    {"msg": "SUBSCRIBE", "protocol": "sip", "dir": "u"},
                    {"msg": "200 OK[SUBSCRIBE]", "protocol": "sip", "dir": "D"},
                    {"msg": "NOTIFY", "protocol": "sip", "dir": "D"},
                    {"msg": "200 OK[NOTIFY]", "protocol": "sip", "dir": "u"},
                ],
                "prerequisites": ["PDU session"]
            },
        }

        # 运行时状态跟踪
        self.active_flows = {}
        self.completed_flows = []
        self.over_flows = []

    def parse_log(self, file_path: str) -> list:
        """解析日志文件（基于制表符分隔的格式）"""
        logs = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # 严格按制表符拆分字段
                parts = line.strip().split('\t')
                
                # 验证字段数量（根据样例日志至少有9个字段）
                if len(parts) < 9:
                    print(f"行 {line_num} 字段不足: {line.strip()}")
                    continue
                
                try:
                    # 解析复合时间戳字段（格式：09:42:30.804, 2025-04-07）
                    start_time_str = parts[2].replace(',', '').strip()  # 09:42:30.804 2025-04-07
                    # end_time_str = parts[3].replace(',', '').strip()
                    
                    # 解析时间戳（使用第一个时间戳作为基准）
                    timestamp = datetime.strptime(start_time_str, "%H:%M:%S.%f %Y-%m-%d")
                    
                    # 构建日志条目
                    log_entry = {
                        # "line_num": line_num,
                        "seq": int(parts[0]),
                        "timestamp": timestamp,
                        # "duration": datetime.strptime(end_time_str, "%H:%M:%S.%f %Y-%m-%d") - timestamp,
                        "protocol": parts[6],  # 第7个字段是协议类型
                        "direction": parts[5], # 第6个字段是方向(U/D)
                        "message": parts[8].strip().lower()  # 直接处理原始消息
                        # "raw": line.strip()
                    }
                    logs.append(log_entry)
                    
                except Exception as e:
                    print(f"解析错误 行 {line_num}: {line.strip()}")
                    print(f"错误详情: {str(e)}")
        return logs

    def analyze_flow_completeness(self, logs):
        """分析日志中的流程完整性"""
        # 初始化所有流程的跟踪状态
        flow_status = {name: {"found_steps": [], "completed": False} for name in self.flow_definitions}
        
        for log_entry in logs:
            for flow_name, flow_def in self.flow_definitions.items():
                # 跳过已完成的流程
                if flow_status[flow_name]["completed"]:
                    continue
                
                # 检查前置条件是否满足
                if not all(p in self.completed_flows for p in flow_def["prerequisites"]):
                    continue
                
                # 检查当前步骤是否匹配
                expected_steps = flow_def["steps"]
                current_step_index = len(flow_status[flow_name]["found_steps"])
                
                if current_step_index < len(expected_steps):
                    expected = expected_steps[current_step_index]
                    if (expected["msg"].lower() in log_entry["message"].lower() and
                        log_entry["protocol"].lower() == expected["protocol"].lower() and
                        log_entry["direction"].lower() == expected["dir"].lower()):
                        
                        # 记录找到的步骤
                        flow_status[flow_name]["found_steps"].append({
                            "step": expected,
                            "timestamp": log_entry["timestamp"]
                        })
                        
                        # 标记完成状态
                        if len(flow_status[flow_name]["found_steps"]) == len(expected_steps):
                            flow_status[flow_name]["completed"] = True
                            self.completed_flows.append(flow_name)
                            if flow_name in self.active_flows:
                                del self.active_flows[flow_name]

        # 更新激活流程状态
        for flow_name in self.flow_definitions:
            if flow_name in self.completed_flows:
                continue
            if len(flow_status[flow_name]["found_steps"]) > 0:
                self.active_flows[flow_name] = {
                    "progress": flow_status[flow_name]["found_steps"],
                    "total_steps": len(self.flow_definitions[flow_name]["steps"])
                }

    def generate_analysis_report(self):
        """生成分析报告"""
        report = {
            "summary": {
                "total_flows": len(self.flow_definitions),
                "completed": len(self.completed_flows),
                "in_progress": len(self.active_flows),
                "not_started": len(self.flow_definitions) - len(self.completed_flows) - len(self.active_flows)
            },
            "completed_flows": [],
            "in_progress_flows": [],
            "problematic_flows": []
        }

            # 已完成流程详情
        for flow_name in self.completed_flows:
                report["completed_flows"].append({
                    "flow_name": flow_name,
                    "steps": self.flow_definitions[flow_name]["steps"],
                    "status": "fully completed"
                })

            # 进行中流程详情
        for flow_name, progress in self.active_flows.items():
                flow_info = {
                    "flow_name": flow_name,
                    "completed_steps": len(progress["progress"]),
                    "total_steps": progress["total_steps"],
                    "last_step_time": progress["progress"][-1]["timestamp"] if progress["progress"] else None,
                    "missing_steps": []
                }
                
                # 找出缺失的步骤
                expected_steps = self.flow_definitions[flow_name]["steps"]
                for idx, step in enumerate(expected_steps):
                    if idx >= len(progress["progress"]):
                        flow_info["missing_steps"].append(step)
                
                report["in_progress_flows"].append(flow_info)

            # 问题流程检测（前置条件满足但未启动）
        for flow_name in self.flow_definitions:
                if flow_name in self.completed_flows or flow_name in self.active_flows:
                    continue
                    
                prerequisites_met = all(p in self.completed_flows for p in self.flow_definitions[flow_name]["prerequisites"])
                if prerequisites_met:
                    report["problematic_flows"].append({
                        "flow_name": flow_name,
                        "issue": "Prerequisites met but flow not started",
                        "missing_initial_step": self.flow_definitions[flow_name]["steps"][0]
                    })

        return report

# 修改后的打印部分
def print_custom_report(report):
    """根据完成状态定制化打印报告"""
    custom_report = {
        "summary": report["summary"],
        "flows": {}
    }
    
    # 处理已完成流程
    for flow in report["completed_flows"]:
        custom_report["flows"][flow["flow_name"]] = "completed"
    
    # 处理进行中流程
    for flow in report["in_progress_flows"]:
        custom_report["flows"][flow["flow_name"]] = {
            "status": "in_progress",
            "progress": f"{flow['completed_steps']}/{flow['total_steps']}",
            "missing_steps": [step["msg"] for step in flow["missing_steps"]],
            "last_step_time": flow["last_step_time"].isoformat() if flow["last_step_time"] else None
        }
    
    # 处理问题流程
    for flow in report["problematic_flows"]:
        custom_report["flows"][flow["flow_name"]] = {
            "status": "problematic",
            "issue": flow["issue"],
            "expected_first_step": flow["missing_initial_step"]["msg"]
        }
    
    # 处理未提及的流程（未开始）
    all_flows = set(analyzer.flow_definitions.keys())
    reported_flows = set(custom_report["flows"].keys())
    for flow_name in all_flows - reported_flows:
        custom_report["flows"][flow_name] = {
            "status": "not_started",
            "reason": "Prerequisites not fulfilled"
        }
    
    print(json.dumps(custom_report, indent=4, default=str))

# 使用示例
analyzer = ProtocolAnalyzer()
logs = analyzer.parse_log("xingwang/rizhi/A0016-1492-KEL-CX36-数据 - 副本.txt")
analyzer.analyze_flow_completeness(logs)
report = analyzer.generate_analysis_report()
print_custom_report(report)