from datetime import datetime
from collections import deque

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

    def analyze_flows(self, logs: list) -> dict:
        """多流程顺序分析"""
        # 按时间排序日志
        sorted_logs = sorted(logs, key=lambda x: x["timestamp"])
        
        # 初始化待处理队列
        flow_queue = deque(sorted_logs)
        
        while flow_queue:
            log = flow_queue.popleft()
            # 检查当前日志是否匹配任何流程步骤
            for flow_name, flow_def in self.flow_definitions.items():
                if not self._check_prerequisites(flow_name):
                    continue
                
                # 确保满足前置条件的流程被激活
                if flow_name not in self.active_flows:
                    self.active_flows[flow_name] = {
                        "current_step": 0,
                        "start_time": None,
                        "steps": []
                    }
                current_state = self.active_flows[flow_name]
                
                expected_step = flow_def["steps"][current_state["current_step"]]
                
                # 多条件匹配
                if (expected_step["msg"].lower() in log["message"].lower() and
                    log["protocol"].lower() == expected_step["protocol"].lower() and
                    log["direction"].lower() == expected_step["dir"].lower()):
                    
                    # 更新流程状态
                    if current_state["start_time"] is None:
                        current_state["start_time"] = log["timestamp"]
                    
                    current_state["steps"].append({
                        "timestamp": log["timestamp"],
                        "log": log
                    })
                    current_state["current_step"] += 1
                    
                    # 检查流程是否完成
                    if current_state["current_step"] == len(flow_def["steps"]):
                        self.completed_flows.append({
                            "flow_name": flow_name,
                            "status": "completed",
                            "duration": log["timestamp"] - current_state["start_time"],
                            "steps": current_state["steps"]
                        })
                        del self.active_flows[flow_name]
                    else:
                        self.active_flows[flow_name] = current_state
                        
        # 处理未完成的流程
        for flow_name, state in self.active_flows.items():
            self.completed_flows.append({
                "flow_name": flow_name,
                "status": "incomplete",
                "progress": f"{state['current_step']}/{len(self.flow_definitions[flow_name]['steps'])}",
                "missing_steps": self.flow_definitions[flow_name]['steps'][state['current_step']:],
                "last_step_time": state["steps"][-1]["timestamp"] if state["steps"] else None
            })
        
        return self._generate_report()

    def _check_prerequisites(self, flow_name: str) -> bool:
        """检查流程前置条件"""
        required_flows = self.flow_definitions[flow_name]["prerequisites"]
        return all(
            any(f["flow_name"] == req and f["status"] == "completed" 
                for f in self.completed_flows)
            for req in required_flows
        )

    def _generate_report(self) -> dict:
        """生成结构化报告"""
        report = {
            "completed": [],
            "incomplete": [],
            "statistics": {
                "total_flows": len(self.flow_definitions),
                "completed_flows": 0,
                "success_rate": 0.0
            }
        }
        
        for flow in self.completed_flows:
            if flow["status"] == "completed":
                report["completed"].append({
                    "flow": flow["flow_name"],
                    "duration": str(flow["duration"]),
                    "steps_count": len(flow["steps"])
                })
                report["statistics"]["completed_flows"] += 1
            else:
                report["incomplete"].append({
                    "flow": flow["flow_name"],
                    "progress": flow["progress"],
                    "next_expected_step": flow["missing_steps"][0]["msg"] if flow["missing_steps"] else None
                })
        
        report["statistics"]["success_rate"] = (
            report["statistics"]["completed_flows"] / report["statistics"]["total_flows"]
            if report["statistics"]["total_flows"] > 0 else 0.0
        )
        
        return report

    def print_report(self, report: dict):
        """增强版报告输出"""
        print("\n" + "="*50)
        print("5G Protocol Flow Analysis Report")
        print("="*50)
        
        # 统计信息
        print(f"\n📊 Statistics:")
        print(f"  - Total Flows Defined: {report['statistics']['total_flows']}")
        print(f"  - Completed Flows: {report['statistics']['completed_flows']}")
        print(f"  - Success Rate: {report['statistics']['success_rate']:.1%}")
        
        # 已完成流程
        if report['completed']:
            print("\n✅ Completed Flows:")
            for flow in report['completed']:
                print(f"\n🔹 {flow['flow']}")
                print(f"   Duration: {flow['duration']}")
                print(f"   Steps Executed: {flow['steps_count']}")
        
        # 未完成流程
        if report['incomplete']:
            print("\n❌ Incomplete Flows:")
            for flow in report['incomplete']:
                print(f"\n🔸 {flow['flow']}")
                print(f"   Progress: {flow['progress']}")
                if flow['next_expected_step']:
                    print(f"   Next Expected Step: {flow['next_expected_step']}")

# 使用示例
if __name__ == "__main__":
    analyzer = ProtocolAnalyzer()
    
    # 从文件解析日志
    logs = analyzer.parse_log("xingwang/rizhi/A0007-1504-KEL-CX30029-54-0.45相控阵-数据-9005.txt")
    
    # 分析流程完整性
    results = analyzer.analyze_flows(logs)
    
    # 生成报告
    analyzer.print_report(results)