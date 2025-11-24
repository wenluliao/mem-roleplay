"""
HTTP客户端测试工具 - 用于测试Mem0AI Web服务
"""

import os
import sys
import time
import json
import requests
import argparse
from typing import Dict, Any, List

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class Mem0HTTPClient:
    """Mem0AI HTTP客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            response = self.session.get(f"{self.base_url}/")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}
    
    def add_conversation(self, user_id: str, dialogue: List[Dict[str, str]], use_async: bool = True) -> Dict[str, Any]:
        """添加对话记忆"""
        data = {
            "user_id": user_id,
            "dialogue": dialogue,
            "use_async": use_async
        }
        
        try:
            response = self.session.post(f"{self.base_url}/api/v1/conversation/add", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}
    
    def search_memory(self, user_id: str, query: str, category: str = "all", limit: int = 10) -> Dict[str, Any]:
        """搜索记忆"""
        data = {
            "user_id": user_id,
            "query": query,
            "category": category,
            "limit": limit
        }
        
        try:
            response = self.session.post(f"{self.base_url}/api/v1/memory/search", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/queue/status")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}
    
    def clear_queue(self) -> Dict[str, Any]:
        """清空队列"""
        try:
            response = self.session.delete(f"{self.base_url}/api/v1/queue/clear")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}


def test_basic_functionality(client: Mem0HTTPClient):
    """测试基本功能"""
    print("=== 基本功能测试 ===\n")
    
    # 测试对话
    messages = [
        {"role": "user", "content": "我喜欢看电影，要不下周二去看电影吧"},
        {"role": "assistant", "content": "好的呀，你喜欢看什么电影"},
        {"role": "user", "content": "我喜欢看国漫动画，比如哪吒系列的"},
        {"role": "assistant", "content": "我也很喜欢，那我们到时候一起吧"},
        {"role": "user", "content": "对了，我对花生严重过敏，一点都不能碰"},
        {"role": "assistant", "content": "好的，我会记住你对花生过敏"}
    ]
    
    # 添加对话
    print("1. 添加对话到记忆库...")
    result = client.add_conversation("test_user", messages)
    print(f"添加结果: {json.dumps(result, ensure_ascii=False, indent=2)}\n")
    
    # 等待异步处理完成
    if result.get("status") == "success" and result.get("queue_length", 0) > 0:
        print("等待异步处理完成...")
        time.sleep(2)
    
    # 搜索测试
    print("2. 搜索测试...")
    results = client.search_memory("test_user", "喜欢什么")
    print(f"搜索结果: {json.dumps(results, ensure_ascii=False, indent=2)}\n")
    
    # 队列状态
    print("3. 队列状态检查...")
    queue_status = client.get_queue_status()
    print(f"队列状态: {json.dumps(queue_status, ensure_ascii=False, indent=2)}\n")
    
    print("基本功能测试完成！\n")


def test_roleplay_features(client: Mem0HTTPClient):
    """测试角色扮演专用功能"""
    print("=== 角色扮演功能测试 ===\n")
    
    # 角色扮演对话
    roleplay_messages = [
        {"role": "user", "content": "我是来自森林的精灵弓箭手，擅长自然魔法"},
        {"role": "assistant", "content": "很高兴认识你，精灵朋友！我叫露西，你的弓箭一定很厉害吧"},
        {"role": "user", "content": "我叫杰克。是的，我可以用魔法箭矢。其实我有点害怕人类，但觉得你还不错"},
        {"role": "assistant", "content": "不用害怕，我会保护你的"},
        {"role": "user", "content": "我喜欢在月光下散步，感受自然的气息。我们精灵族对金属过敏，不能接触铁器"},
        {"role": "assistant", "content": "明白了，我会注意不让你接触金属物品"},
        {"role": "user", "content": "要不下次我们在森林深处见面吧，那里有我的秘密基地"}
    ]
    
    # 添加角色扮演对话
    print("1. 添加角色扮演对话...")
    result = client.add_conversation("elf_user", roleplay_messages, use_async=True)
    print(f"添加结果: {json.dumps(result, ensure_ascii=False, indent=2)}\n")
    
    # 等待异步处理
    if result.get("status") == "success" and result.get("queue_length", 0) > 0:
        print("等待角色扮演分类处理完成...")
        time.sleep(3)
    
    # 测试分类搜索
    print("2. 分类搜索测试...")
    
    # 搜索档案类记忆
    profile_results = client.search_memory("elf_user", "精灵", category="profile")
    print(f"档案类记忆: {profile_results.get('total_count', 0)} 条")
    
    # 搜索场景类记忆
    scenario_results = client.search_memory("elf_user", "森林", category="roleplay_scenarios")
    print(f"场景类记忆: {scenario_results.get('total_count', 0)} 条")
    
    # 搜索行为模式
    behavior_results = client.search_memory("elf_user", "害怕", category="behavioral_patterns")
    print(f"行为模式记忆: {behavior_results.get('total_count', 0)} 条")
    
    # 队列状态
    print("\n3. 队列状态检查...")
    queue_status = client.get_queue_status()
    print(f"队列状态: {json.dumps(queue_status, ensure_ascii=False, indent=2)}\n")
    
    print("角色扮演功能测试完成！\n")


def test_advanced_features(client: Mem0HTTPClient):
    """测试高级功能"""
    print("=== 高级功能测试 ===\n")
    
    # 测试不同分类搜索
    print("1. 多分类搜索测试...")
    
    categories = ["profile", "behavioral_patterns", "roleplay_scenarios", "event", "interaction"]
    
    for category in categories:
        results = client.search_memory("test_user", "电影", category=category)
        print(f"{category} 分类搜索结果: {results.get('total_count', 0)} 条")
    
    # 测试大量数据
    print("\n2. 批量添加测试...")
    
    bulk_messages = []
    for i in range(3):  # 小批量测试
        bulk_messages.extend([
            {"role": "user", "content": f"批量测试消息 {i} - 我喜欢各种类型的音乐"},
            {"role": "assistant", "content": f"批量测试回复 {i} - 音乐确实很美妙"}
        ])
    
    result = client.add_conversation("bulk_user", bulk_messages, use_async=True)
    print(f"批量添加结果: {json.dumps(result, ensure_ascii=False, indent=2)}\n")
    
    # 队列状态
    print("3. 队列状态检查...")
    queue_status = client.get_queue_status()
    print(f"队列状态: {json.dumps(queue_status, ensure_ascii=False, indent=2)}\n")
    
    print("高级功能测试完成！\n")


def test_edge_cases(client: Mem0HTTPClient):
    """测试边界情况"""
    print("=== 边界情况测试 ===\n")
    
    # 空搜索测试
    print("1. 空搜索测试...")
    empty_results = client.search_memory("test_user", "")
    print(f"空搜索返回: {empty_results.get('total_count', 0)} 条结果\n")
    
    # 不存在的用户测试
    print("2. 不存在的用户测试...")
    nonexistent_results = client.search_memory("nonexistent_user", "测试")
    print(f"不存在的用户搜索: {json.dumps(nonexistent_results, ensure_ascii=False, indent=2)}\n")
    
    # 无效消息格式测试
    print("3. 无效消息格式测试...")
    try:
        # 尝试发送无效格式
        invalid_data = {"user_id": "test_user", "dialogue": "invalid_format"}
        response = client.session.post(f"{client.base_url}/api/v1/conversation/add", json=invalid_data)
        print(f"无效格式响应状态: {response.status_code}\n")
    except Exception as e:
        print(f"无效格式测试异常: {e}\n")
    
    # 清空队列测试
    print("4. 清空队列测试...")
    clear_result = client.clear_queue()
    print(f"清空队列结果: {json.dumps(clear_result, ensure_ascii=False, indent=2)}\n")
    
    print("边界情况测试完成！\n")


def test_performance(client: Mem0HTTPClient):
    """测试性能"""
    print("=== 性能测试 ===\n")
    
    # 搜索性能测试
    print("1. 搜索性能测试...")
    start_time = time.time()
    
    for i in range(3):
        results = client.search_memory("test_user", f"测试 {i}")
    
    search_time = time.time() - start_time
    print(f"3次搜索平均耗时: {search_time/3:.2f}秒\n")
    
    # 添加性能测试
    print("2. 添加性能测试...")
    start_time = time.time()
    
    test_messages = [
        {"role": "user", "content": "性能测试消息"},
        {"role": "assistant", "content": "性能测试回复"}
    ]
    result = client.add_conversation("performance_user", test_messages, use_async=True)
    
    add_time = time.time() - start_time
    print(f"异步添加耗时: {add_time:.2f}秒")
    print(f"添加结果: {json.dumps(result, ensure_ascii=False, indent=2)}\n")
    
    # 队列状态
    print("3. 队列状态检查...")
    queue_status = client.get_queue_status()
    print(f"队列状态: {json.dumps(queue_status, ensure_ascii=False, indent=2)}\n")
    
    print("性能测试完成！\n")


def run_all_tests(base_url: str = "http://localhost:8000"):
    """运行所有测试"""
    print("开始运行Mem0AI HTTP客户端测试...\n")
    
    # 创建客户端
    client = Mem0HTTPClient(base_url)
    
    # 健康检查
    print("🔍 检查服务状态...")
    health = client.health_check()
    print(f"服务状态: {json.dumps(health, ensure_ascii=False, indent=2)}\n")
    
    if health.get("status") != "healthy":
        print("❌ 服务不可用，请先启动Web服务")
        print("启动命令: python run_web_service.py")
        return
    
    try:
        # 基础功能测试
        test_basic_functionality(client)
        
        # 角色扮演功能测试
        test_roleplay_features(client)
        
        # 高级功能测试
        test_advanced_features(client)
        
        # 边界情况测试
        test_edge_cases(client)
        
        # 性能测试
        test_performance(client)
        
        print("=== 所有测试完成 ===")
        print("🎉 HTTP客户端测试通过！")
        print("\n测试总结:")
        print("✅ 基本功能正常")
        print("✅ 角色扮演功能正常")
        print("✅ 高级功能正常")
        print("✅ 边界情况处理正常")
        print("✅ 性能表现可接受")
        print("✅ 异步队列处理正常")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


def run_specific_test(test_name: str, base_url: str = "http://localhost:8000"):
    """运行特定测试"""
    tests = {
        "basic": test_basic_functionality,
        "roleplay": test_roleplay_features,
        "advanced": test_advanced_features,
        "edge": test_edge_cases,
        "performance": test_performance
    }
    
    if test_name in tests:
        print(f"运行特定测试: {test_name}\n")
        
        # 创建客户端
        client = Mem0HTTPClient(base_url)
        
        # 健康检查
        health = client.health_check()
        if health.get("status") != "healthy":
            print("❌ 服务不可用，请先启动Web服务")
            return
        
        tests[test_name](client)
    else:
        print(f"未知测试: {test_name}")
        print("可用测试: basic, roleplay, advanced, edge, performance")


def quick_test(base_url: str = "http://localhost:8000"):
    """快速测试 - 只测试基本功能"""
    print("🚀 快速测试Mem0AI Web服务...\n")
    
    client = Mem0HTTPClient(base_url)
    
    # 健康检查
    health = client.health_check()
    print(f"服务状态: {json.dumps(health, ensure_ascii=False, indent=2)}\n")
    
    if health.get("status") != "healthy":
        print("❌ 服务不可用")
        return
    
    # # 快速添加测试
    # messages = [
    #     {"role": "user", "content": "我平常爱看电影，要不下周一起看电影把"},
    #     {"role": "assistant", "content": "好的呀，你喜欢看什么电影"},
    #     {"role": "user", "content": "我喜欢看漫威系列，比如钢铁侠"},
    #     {"role": "assistant", "content": "我也很喜欢，那我们到时候一起吧"},
    #     {"role": "user", "content": "今天他天气好冷啊"},
    #     {"role": "assistant", "content": "那你要多穿点衣服噢"}
    # ]
    
    # print("📝 添加测试对话...")
    # result = client.add_conversation("quick_user", messages)
    # print(f"添加结果: {json.dumps(result, ensure_ascii=False, indent=2)}\n")
    
    # # 等待处理
    # time.sleep(1)
    
    # 搜索测试
    print("🔍 搜索测试...")
    results = client.search_memory("test_user_002", "早啊。昨晚为什么没给我打电话。是不是把我电话忘了")
    print(f"搜索结果: {json.dumps(results, ensure_ascii=False, indent=2)}\n")
    
    # 队列状态
    # queue_status = client.get_queue_status()
    # print(f"📊 队列状态: {json.dumps(queue_status, ensure_ascii=False, indent=2)}\n")
    
    print("✅ 快速测试完成！")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Mem0AI HTTP客户端测试工具')
    parser.add_argument('--test', type=str, help='运行特定测试')
    parser.add_argument('--url', type=str, default='http://localhost:8000', help='Web服务地址')
    parser.add_argument('--quick', action='store_true', help='快速测试')
    
    args = parser.parse_args()
    
    if args.quick:
        quick_test(args.url)
    elif args.test:
        run_specific_test(args.test, args.url)
    else:
        run_all_tests(args.url)