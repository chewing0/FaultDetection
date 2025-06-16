from logany import result_out

def errorlist():
    error_list = {
        'all_flows_completed': '未发现问题',
        'in_progress': '协议子流程执行不完整',
        'problematic': '协议子流程未执行',
        'prereq_missing': '协议子流程缺失'

    }
    result = result_out()
    print('-'*50)
    if result['status'] == 'all_flows_completed':
        print(error_list[result['status']])
    else:
        print(error_list[result['status']])
        print(f"未完成的流程: {result['blocking_flow']}")
        print(f"状态: {result['status']}")
        if 'status_details' in result:
            print("详细信息:")
            for key, value in result['status_details'].items():
                print(f"{key}: {value}")
    print('-'*50)

if __name__ == '__main__':
    errorlist()