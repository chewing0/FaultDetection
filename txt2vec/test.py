import text2vec as t2v
import time

def show_menu():
    print("\n" + "="*40)
    print("日志异常检测系统")
    print("="*40)
    print("1. 异常检测（与正常日志对比）")
    print("2. 故障类型识别（与故障库对比）")
    print("3. 添加异常日志到故障库")
    print("0. 退出程序")
    print("="*40)
    return input("请选择功能 (0-3): ")

def anomaly_detection():
    """异常检测：通过与正常日志对比来检测是否存在异常"""
    print("\n" + "="*40)
    print("异常检测")
    print("="*40)
    t2v.Anomaly_Detection()

def fault_identification():
    """故障识别：将日志与故障库对比来识别故障类型"""
    print("\n" + "="*40)
    print("故障类型识别")
    print("="*40)
    # 获取故障库数据
    vectors, errs = t2v.csv_reader()
    # 获取当前日志向量
    log_vec = t2v.get_logvec()
    # 获取可能的错误类型
    errtype = t2v.error_type(log_vec, vectors, errs)
    print(f"\n预测的故障类型: {errtype}")

def add_to_database():
    """添加新的异常日志到故障库"""
    print("\n" + "="*40)
    print("添加异常日志到故障库")
    print("="*40)
    t2v.vec_save()
    print("\n已成功添加到故障库！")

def main():
    while True:
        start_time = time.time()
        choice = show_menu()
        
        if choice == '0':
            print("\n感谢使用！再见！")
            break
        elif choice == '1':
            anomaly_detection()
        elif choice == '2':
            fault_identification()
        elif choice == '3':
            add_to_database()
        else:
            print("\n无效的选择，请重新输入！")
            continue

        end_time = time.time()
        print("\n" + "="*40)
        print(f"操作耗时: {end_time - start_time:.2f}秒")
        print("="*40)
        
        input("\n按回车键继续...")

if __name__ == "__main__":
    main()