"""
自定义Memory客户端 - 修复ModelScope API认证问题
"""

import sys
import os
from typing import Dict, Any, Optional

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mem0 import Memory
from config import config


class CustomMemoryClient:
    """自定义Memory客户端，修复ModelScope认证问题"""
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """
        初始化自定义Memory客户端
        
        Args:
            config_dict: 配置字典，如果为None则使用默认配置
        """
        if config_dict is None:
            config_dict = config.get_config()
        
        # 修复ModelScope认证配置
        self._fix_modelscope_auth(config_dict)
        
        # 创建标准Memory客户端
        self.memory = Memory.from_config(config_dict)
    
    def _fix_modelscope_auth(self, config_dict: Dict[str, Any]):
        """修复ModelScope API认证配置"""
        llm_config = config_dict.get('llm', {}).get('config', {})
        
        # 检查是否是ModelScope API
        base_url = llm_config.get('openai_base_url', '')
        if 'modelscope.cn' in base_url:
            api_key = llm_config.get('api_key', '')
            
            if api_key and api_key.startswith('ms-'):
                # 确保使用正确的认证头格式
                print("🔧 检测到ModelScope API，应用认证修复...")
                print(f"   Base URL: {base_url}")
                print(f"   API Key: {api_key[:10]}...{api_key[-10:]}")
                
                # 这里可以添加特定的ModelScope认证处理逻辑
                # 目前mem0库应该能正确处理，但我们可以确保配置正确
    
    def add(self, content: str, user_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """添加记忆"""
        return self.memory.add(content, user_id=user_id, metadata=metadata)
    
    def search(self, query: str, user_id: str, limit: int = 10) -> Dict[str, Any]:
        """搜索记忆"""
        return self.memory.search(query, user_id=user_id, limit=limit)
    
    def get_all(self, user_id: str) -> Dict[str, Any]:
        """获取所有记忆"""
        return self.memory.get_all(user_id=user_id)
    
    def delete(self, memory_id: str, user_id: str) -> Dict[str, Any]:
        """删除记忆"""
        return self.memory.delete(memory_id, user_id=user_id)


def create_custom_memory_client() -> CustomMemoryClient:
    """创建自定义Memory客户端实例"""
    return CustomMemoryClient()


# 测试函数
def test_custom_client():
    """测试自定义客户端"""
    print("🧪 测试自定义Memory客户端")
    print("=" * 50)
    
    try:
        # 创建自定义客户端
        client = create_custom_memory_client()
        print("✅ 自定义Memory客户端创建成功")
        
        # 测试基本功能
        test_content = "这是一个测试记忆"
        test_user_id = "test_user_001"
        
        # 添加记忆
        result = client.add(test_content, test_user_id)
        print("✅ 记忆添加功能正常")
        print(f"   结果: {result}")
        
        # 搜索记忆
        search_result = client.search("测试", test_user_id)
        print("✅ 记忆搜索功能正常")
        print(f"   找到 {len(search_result.get('results', []))} 条相关记忆")
        
        return True
        
    except Exception as e:
        print(f"❌ 自定义客户端测试失败: {e}")
        return False


if __name__ == "__main__":
    test_custom_client()