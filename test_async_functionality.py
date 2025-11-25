#!/usr/bin/env python3
"""
测试异步功能是否正常工作
"""
import requests
import json
import time

def test_async_functionality():
    """测试异步功能"""
    base_url = "http://localhost:8000"
    
    print("🧪 开始测试异步功能...")
    
    # 测试数据
    test_conversation = [
        {"role": "user", "content": "你好，我是小明"},
        {"role": "assistant", "content": "你好小明，我是AI助手"},
        {"role": "user", "content": "我喜欢打篮球"},
        {"role": "assistant", "content": "篮球是一项很好的运动"}
    ]
    
    # 测试异步模式
    print("\n1. 测试异步模式（use_async=True）...")
    async_data = {
        "conversation": test_conversation,
        "user_id": "test_user_async",
        "user_name": "测试用户异步",
        "use_async": True
    }
    
    start_time = time.time()
    try:
        response = requests.post(f"{base_url}/api/v1/conversation/add", json=async_data)
        async_response_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 异步请求成功 - 响应时间: {async_response_time:.3f}秒")
            print(f"   状态: {result['status']}")
            print(f"   消息: {result['message']}")
            print(f"   处理模式: {result['processing_mode']}")
            print(f"   任务ID: {result.get('task_id', 'N/A')}")
            print(f"   队列长度: {result.get('queue_length', 0)}")
        else:
            print(f"❌ 异步请求失败 - 状态码: {response.status_code}")
            print(f"   错误信息: {response.text}")
    except Exception as e:
        print(f"❌ 异步请求异常: {e}")
    
    # 测试同步模式
    print("\n2. 测试同步模式（use_async=False）...")
    sync_data = {
        "conversation": test_conversation,
        "user_id": "test_user_sync", 
        "user_name": "测试用户同步",
        "use_async": False
    }
    
    start_time = time.time()
    try:
        response = requests.post(f"{base_url}/api/v1/conversation/add", json=sync_data)
        sync_response_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 同步请求成功 - 响应时间: {sync_response_time:.3f}秒")
            print(f"   状态: {result['status']}")
            print(f"   消息: {result['message']}")
            print(f"   处理模式: {result['processing_mode']}")
            print(f"   添加数量: {result.get('added_count', 0)}")
        else:
            print(f"❌ 同步请求失败 - 状态码: {response.status_code}")
            print(f"   错误信息: {response.text}")
    except Exception as e:
        print(f"❌ 同步请求异常: {e}")
    
    # 检查队列状态
    print("\n3. 检查队列状态...")
    try:
        response = requests.get(f"{base_url}/api/v1/queue/status")
        if response.status_code == 200:
            queue_status = response.json()
            print(f"✅ 队列状态查询成功")
            print(f"   队列状态: {json.dumps(queue_status, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 队列状态查询失败 - 状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 队列状态查询异常: {e}")
    
    # 对比响应时间
    print("\n4. 响应时间对比:")
    print(f"   异步模式响应时间: {async_response_time:.3f}秒")
    print(f"   同步模式响应时间: {sync_response_time:.3f}秒")
    
    if async_response_time < sync_response_time:
        print("✅ 异步模式响应更快，符合预期")
    else:
        print("⚠️  异步模式响应时间较长，可能需要进一步优化")

if __name__ == "__main__":
    test_async_functionality()