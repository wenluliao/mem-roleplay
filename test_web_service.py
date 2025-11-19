"""
Mem0AI Web服务综合测试脚本
可以启动Web服务并运行HTTP客户端测试
"""

import os
import sys
import time
import subprocess
import threading
import requests
import json
from pathlib import Path

# 添加src和test目录到Python路径
src_path = Path(__file__).parent / "src"
test_path = Path(__file__).parent / "test"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(test_path))


def check_service_health(base_url: str = "http://localhost:8000", timeout: int = 30) -> bool:
    """检查Web服务是否健康"""
    print("🔍 检查Web服务状态...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{base_url}/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    print("✅ Web服务运行正常")
                    return True
        except requests.exceptions.RequestException:
            pass
        
        print(".", end="", flush=True)
        time.sleep(1)
    
    print("\n❌ Web服务启动超时")
    return False


def start_web_service():
    """启动Web服务"""
    print("🚀 启动Mem0AI Web服务...")
    
    try:
        # 使用subprocess启动Web服务
        process = subprocess.Popen([
            sys.executable, "run_web_service.py", 
            "--host", "localhost", 
            "--port", "8000",
            "--reload"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # 等待服务启动
        if check_service_health():
            print("✅ Web服务启动成功")
            return process
        else:
            print("❌ Web服务启动失败")
            process.terminate()
            return None
            
    except Exception as e:
        print(f"❌ 启动Web服务时出错: {e}")
        return None


def run_http_tests():
    """运行HTTP客户端测试"""
    print("\n🧪 运行HTTP客户端测试...")
    
    try:
        # 导入并运行HTTP测试
        from test.test_http_client import run_all_tests
        run_all_tests("http://localhost:8000")
        return True
    except Exception as e:
        print(f"❌ HTTP测试运行失败: {e}")
        return False


def run_quick_test():
    """运行快速测试"""
    print("\n⚡ 运行快速测试...")
    
    try:
        from test.test_http_client import quick_test
        quick_test("http://localhost:8000")
        return True
    except Exception as e:
        print(f"❌ 快速测试运行失败: {e}")
        return False


def test_with_existing_service():
    """测试已运行的Web服务"""
    print("🔗 连接到已运行的Web服务...")
    
    if check_service_health():
        print("\n选择测试模式:")
        print("1. 完整测试")
        print("2. 快速测试")
        print("3. 角色扮演测试")
        
        choice = input("请输入选择 (1-3): ").strip()
        
        if choice == "1":
            return run_http_tests()
        elif choice == "2":
            return run_quick_test()
        elif choice == "3":
            try:
                from test.test_http_client import run_specific_test
                run_specific_test("roleplay", "http://localhost:8000")
                return True
            except Exception as e:
                print(f"❌ 角色扮演测试失败: {e}")
                return False
        else:
            print("❌ 无效选择")
            return False
    else:
        print("❌ 没有找到运行的Web服务")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 Mem0AI Web服务综合测试工具")
    print("=" * 60)
    
    print("\n选择操作模式:")
    print("1. 启动Web服务并运行完整测试")
    print("2. 运行快速测试")
    print("3. 连接到已运行的Web服务进行测试")
    print("4. 仅启动Web服务")
    
    choice = input("\n请输入选择 (1-4): ").strip()
    
    if choice == "1":
        # 模式1：启动服务并运行完整测试
        process = start_web_service()
        if process:
            try:
                success = run_http_tests()
                if success:
                    print("\n🎉 所有测试完成！")
                else:
                    print("\n❌ 测试过程中出现问题")
            finally:
                print("\n🛑 停止Web服务...")
                process.terminate()
    
    elif choice == "2":
        # 模式2：启动服务并运行快速测试
        # process = start_web_service()
        try:
            success = run_quick_test()
            if success:
                print("\n🎉 快速测试完成！")
            else:
                print("\n❌ 快速测试失败")
        finally:
            print("\n🛑 停止Web服务...")
            process.terminate()
    
    elif choice == "3":
        # 模式3：连接到已运行的服务
        test_with_existing_service()
    
    elif choice == "4":
        # 模式4：仅启动服务
        process = start_web_service()
        if process:
            print("\n🌐 Web服务已启动，按Ctrl+C停止服务")
            try:
                process.wait()
            except KeyboardInterrupt:
                print("\n🛑 停止Web服务...")
                process.terminate()
    
    else:
        print("❌ 无效选择")
        return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，退出程序")
    except Exception as e:
        print(f"\n❌ 程序运行出错: {e}")
        import traceback
        traceback.print_exc()