class ProtocolChecker:
    """
    协议流程检查器，基于状态机模型验证执行顺序
    """
    def __init__(self, rules, initial_state, end_states):
        """
        初始化检查器
        :param rules: 状态转移规则字典 
           格式: {当前状态: [允许的下一个状态]}
        :param initial_state: 初始状态
        :param end_states: 终止状态集合
        """
        self.rules = rules
        self.initial_state = initial_state
        self.end_states = end_states

    def validate(self, execution):
        """
        验证执行流程是否合法
        :param execution: 执行步骤列表
        :return: (是否有效, 错误信息)
        """
        if not execution:
            return False, "执行记录不能为空"

        current_state = self.initial_state
        
        # 检查初始步骤
        if execution[0] not in self.rules.get(current_state, []):
            return False, (
                f"初始步骤错误。期望从 {self.initial_state} 出发的步骤，"
                f"实际得到 '{execution[0]}'"
            )

        for step_idx, step in enumerate(execution):
            # 检查未知状态
            if step not in self.rules:
                return False, f"发现未定义的状态 '{step}'"

            # 更新当前状态（下一步才需要检查转移关系）
            if step_idx > 0:
                previous_step = execution[step_idx-1]
                allowed_steps = self.rules.get(previous_step, [])
                
                if step not in allowed_steps:
                    return False, (
                        f"第 {step_idx} 步状态转移错误。"
                        f"从 '{previous_step}' 不能转移到 '{step}'，"
                        f"允许的转移：{allowed_steps}"
                    )

            current_state = step

        # 检查终止状态
        if current_state not in self.end_states:
            return False, (
                f"流程未正确终止。最后状态 '{current_state}' "
                f"不在终止状态集合 {self.end_states} 中"
            )

        return True, "流程验证通过"


if __name__ == "__main__":
    # 示例协议规则定义
    protocol_rules = {
        # 当前状态      允许的下一个状态
        'init':       ['A'],
        'A':          ['B'],
        'B':          ['C', 'D'],
        'C':          ['E'],
        'D':          ['E'],
        'E':          ['end'],
        'end':        []  # 终止状态
    }

    # 创建检查器实例
    checker = ProtocolChecker(
        rules=protocol_rules,
        initial_state='init',
        end_states={'end'}
    )

    # 测试用例
    test_cases = [
        (['A', 'x', 'B', 'C', 'E', 'end'], True),    # 正确流程1
    ]

    # 执行测试
    for execution, expected in test_cases:
        is_valid, message = checker.validate(execution)
        print(f"执行流程: {execution}")
        print(f"预期结果: {expected} 实际结果: {is_valid}")
        if not is_valid:
            print(f"错误信息: {message}")
        print("-" * 50)
