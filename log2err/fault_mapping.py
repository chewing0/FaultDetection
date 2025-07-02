# -*- coding: utf-8 -*-
"""
故障映射规则配置文件
定义了从日志异常状态到故障描述的映射关系
"""

# 故障映射规则字典
FAULT_MAPPING = {
    # 完全未启动的情况
    "Registration Request": {
        "not_started": "启动失败 - 终端无法发起注册请求",
        "prerequisites_not_met": "系统异常 - 注册前置条件检查失败",
        "problematic": "启动异常 - 注册请求发送失败"
    },
    
    # RRC连接问题
    "RRC Connection Setup": {
        "not_started": "卡MSG1 - RRC连接建立未启动",
        "in_progress": "卡MSG1 - RRC连接建立过程中断",
        "problematic": "RRC连接异常 - 连接建立流程异常"
    },
    
    # NAS鉴权问题
    "NAS Authentication": {
        "not_started": "卡MSG2 - NAS鉴权未启动", 
        "in_progress": "卡MSG2 - NAS鉴权过程中断",
        "problematic": "鉴权失败 - NAS鉴权流程异常"
    },
    
    # RRC鉴权问题
    "RRC Authentication": {
        "not_started": "卡MSG3 - RRC鉴权未启动",
        "in_progress": "卡MSG3 - RRC鉴权过程中断", 
        "problematic": "鉴权失败 - RRC鉴权流程异常"
    },
    
    # NAS安全模式问题
    "NAS SMC": {
        "not_started": "卡MSG4 - NAS安全模式配置未启动",
        "in_progress": "卡MSG4 - NAS安全模式配置中断",
        "problematic": "安全配置失败 - NAS安全模式异常"
    },
    
    # UE能力上报问题
    "UE Capability": {
        "not_started": "卡MSG5 - UE能力上报未启动",
        "in_progress": "卡MSG5 - UE能力上报过程中断",
        "problematic": "能力协商失败 - UE能力上报异常"
    },
    
    # RRC安全模式问题
    "RRC SMC": {
        "not_started": "卡MSG6 - RRC安全模式配置未启动",
        "in_progress": "卡MSG6 - RRC安全模式配置中断",
        "problematic": "安全配置失败 - RRC安全模式异常"
    },
    
    # RRC重构问题
    "RRC Reconfig": {
        "not_started": "卡MSG7 - RRC重构未启动",
        "in_progress": "卡MSG7 - RRC重构过程中断",
        "problematic": "配置失败 - RRC重构异常"
    },
    
    # 注册响应问题
    "Registration response": {
        "not_started": "注册失败 - 网络未响应注册请求",
        "in_progress": "注册超时 - 注册响应流程不完整",
        "problematic": "注册异常 - 注册响应流程异常"
    },
    
    # PDU会话问题
    "PDU session": {
        "not_started": "连接失败 - PDU会话建立未启动",
        "in_progress": "连接超时 - PDU会话建立中断", 
        "problematic": "数据连接失败 - PDU会话建立异常"
    },
    
    # SIP注册问题
    "SIP Registration": {
        "not_started": "语音服务不可用 - SIP注册未启动",
        "in_progress": "语音注册超时 - SIP注册过程中断",
        "problematic": "语音服务异常 - SIP注册流程异常"
    }
}

def get_fault_mapping():
    """获取故障映射规则"""
    return FAULT_MAPPING

def get_fault_description(flow_name, status):
    """
    根据流程名称和状态获取故障描述
    
    Args:
        flow_name (str): 流程名称
        status (str): 状态
        
    Returns:
        str: 故障描述，如果未找到则返回None
    """
    if flow_name in FAULT_MAPPING and status in FAULT_MAPPING[flow_name]:
        return FAULT_MAPPING[flow_name][status]
    return None

def add_fault_mapping(flow_name, status, description):
    """
    添加新的故障映射规则
    
    Args:
        flow_name (str): 流程名称
        status (str): 状态
        description (str): 故障描述
    """
    if flow_name not in FAULT_MAPPING:
        FAULT_MAPPING[flow_name] = {}
    FAULT_MAPPING[flow_name][status] = description

def update_fault_mapping(flow_name, status, description):
    """
    更新现有的故障映射规则
    
    Args:
        flow_name (str): 流程名称
        status (str): 状态  
        description (str): 新的故障描述
    """
    if flow_name in FAULT_MAPPING:
        FAULT_MAPPING[flow_name][status] = description
    else:
        add_fault_mapping(flow_name, status, description)

def get_all_flows():
    """获取所有流程名称"""
    return list(FAULT_MAPPING.keys())

def get_flow_statuses(flow_name):
    """获取指定流程的所有状态"""
    if flow_name in FAULT_MAPPING:
        return list(FAULT_MAPPING[flow_name].keys())
    return []
