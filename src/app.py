"""
主应用模块 - 角色扮演优化版
提供高级API和示例用法
"""

import os
from typing import Dict, Any, List, Optional

from .config import config
from .roleplay_smart_memory_manager import RoleplaySmartMemoryManager
from .utils import validation_utils, PerformanceMonitor, LLMLoggingMiddleware, setup_llm_logging

# 创建性能监控实例
performance_monitor = PerformanceMonitor()

# 创建LLM日志记录中间件实例
llm_logging_middleware = LLMLoggingMiddleware()

# 启用LLM日志记录
setup_llm_logging()


class RoleplayMem0App:
    """角色扮演专用的Mem0应用主类"""
    
    def __init__(self, config_overrides: Optional[Dict[str, Any]] = None):
        """
        初始化应用
        
        Args:
            config_overrides: 配置覆盖项
        """
        # 应用配置覆盖
        if config_overrides:
            self._apply_config_overrides(config_overrides)
        
        # 初始化角色扮演智能记忆管理器
        self.smm = RoleplaySmartMemoryManager()
        
        # 应用状态
        self._initialized = True
        print("🎭 角色扮演Mem0应用初始化完成")
    
    def _apply_config_overrides(self, overrides: Dict[str, Any]):
        """应用配置覆盖"""
        for section, values in overrides.items():
            if isinstance(values, dict):
                for key, value in values.items():
                    config.update_config(section, key, value)
    
    @performance_monitor.timeit
    def add_conversation(self, messages: List[Dict[str, str]], user_id: str,
                        conversation_context: Optional[Dict[str, Any]] = None,
                        enable_roleplay_classification: bool = True) -> Dict[str, Any]:
        """
        添加对话到记忆系统（角色扮演优化版）
        
        Args:
            messages: 对话消息列表
            user_id: 用户ID
            conversation_context: 对话上下文
            enable_roleplay_classification: 是否启用角色扮演分类
            
        Returns:
            添加结果
        """
        if enable_roleplay_classification:
            return self.smm.add_conversation_with_roleplay_classification(messages, user_id)
        else:
            return self.smm.add_conversation(messages, user_id, conversation_context)
    
    @performance_monitor.timeit
    def search_memories(self, query: str, user_id: str, 
                    min_importance: Optional[str] = None,
                    exclude_deleted: bool = True,
                    category_filter: Optional[str] = None,
                    limit: Optional[int] = None) -> Dict[str, Any]:  # 添加 limit 参数
        """
        搜索记忆（支持分类过滤）
        """
        if category_filter:
            # 使用分类搜索
            return self.smm.search_by_category(category_filter, user_id)
        else:
            # 使用智能搜索
            results = self.smm.search_smart(query, user_id, min_importance, exclude_deleted)
            # 应用 limit 限制
            if limit and len(results['results']) > limit:
                results['results'] = results['results'][:limit]
                results['total_count'] = limit
            return results
    
    @performance_monitor.timeit
    def update_memory(self, search_query: str, new_content: str, user_id: str,
                     importance: Optional[str] = None,
                     category: Optional[str] = None) -> int:
        """
        更新记忆（支持分类更新）
        
        Args:
            search_query: 搜索查询
            new_content: 新内容
            user_id: 用户ID
            importance: 新的重要性级别
            category: 新的分类类型
            
        Returns:
            更新的记忆数量
        """
        return self.smm.update_memory(search_query, new_content, user_id, importance)
    
    def delete_memory(self, search_query: str, user_id: str,
                     confirm_threshold: float = 0.8) -> int:
        """
        删除记忆
        
        Args:
            search_query: 搜索查询
            user_id: 用户ID
            confirm_threshold: 确认阈值
            
        Returns:
            删除的记忆数量
        """
        return self.smm.delete_memory(search_query, user_id, confirm_threshold)
    
    def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """
        获取记忆统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            统计信息
        """
        return self.smm.get_memory_stats(user_id)
    
    @performance_monitor.timeit
    def cleanup_memories(self, user_id: str) -> Dict[str, int]:
        """
        清理记忆（过期和相似记忆）
        
        Args:
            user_id: 用户ID
            
        Returns:
            清理结果统计
        """
        expired_count = self.smm.cleanup_expired_memories(user_id)
        merged_count = self.smm.merge_similar_memories(user_id)
        
        return {
            "expired_cleaned": expired_count,
            "similar_merged": merged_count
        }
    
    def get_important_memories(self, user_id: str, importance_level: str = "medium") -> Dict[str, Any]:
        """
        获取重要记忆
        
        Args:
            user_id: 用户ID
            importance_level: 重要性级别
            
        Returns:
            重要记忆列表
        """
        return self.smm.get_important_memories(user_id, importance_level)
    
    def get_frequent_memories(self, user_id: str, min_count: int = 2) -> Dict[str, Any]:
        """
        获取频繁访问的记忆
        
        Args:
            user_id: 用户ID
            min_count: 最小访问次数
            
        Returns:
            频繁访问的记忆列表
        """
        return self.smm.get_frequently_accessed(user_id, min_count)
    
    @performance_monitor.timeit
    def search_by_category(self, category: str, user_id: str, 
                          min_confidence: float = 0.0) -> Dict[str, Any]:
        """
        按分类搜索记忆
        
        Args:
            category: 分类类型
            user_id: 用户ID
            min_confidence: 最小分类置信度
            
        Returns:
            分类搜索结果
        """
        return self.smm.search_by_category(category, user_id, min_confidence)
    
    def get_category_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        获取分类统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            分类统计信息
        """
        return self.smm.get_category_statistics(user_id)
    
    # 新增的角色扮演专用方法
    def get_roleplay_profile(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户角色扮演档案
        
        Args:
            user_id: 用户ID
            
        Returns:
            角色档案信息
        """
        profile_memories = self.smm.get_memories_by_roleplay_category(user_id, "profile")
        return {
            "user_id": user_id,
            "profile_memories": profile_memories,
            "total_traits": len(profile_memories["memories"])
        }
    
    def get_behavioral_patterns(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户行为模式
        
        Args:
            user_id: 用户ID
            
        Returns:
            行为模式信息
        """
        pattern_memories = self.smm.get_memories_by_roleplay_category(user_id, "behavioral_patterns")
        return {
            "user_id": user_id,
            "behavioral_patterns": pattern_memories,
            "pattern_count": len(pattern_memories["memories"])
        }
    
    def get_roleplay_context(self, user_id: str) -> Dict[str, Any]:
        """
        获取当前角色扮演上下文
        
        Args:
            user_id: 用户ID
            
        Returns:
            上下文信息
        """
        context_memories = self.smm.get_memories_by_roleplay_category(user_id, "interaction_context")
        internal_thoughts = self.smm.get_memories_by_roleplay_category(user_id, "internal_monologue")
        
        return {
            "user_id": user_id,
            "current_context": context_memories,
            "internal_thoughts": internal_thoughts,
            "context_depth": len(context_memories["memories"]) + len(internal_thoughts["memories"])
        }
    
    def get_preferred_scenarios(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户偏好的角色扮演场景
        
        Args:
            user_id: 用户ID
            
        Returns:
            场景偏好信息
        """
        scenario_memories = self.smm.get_memories_by_roleplay_category(user_id, "roleplay_scenarios")
        return {
            "user_id": user_id,
            "preferred_scenarios": scenario_memories,
            "scenario_count": len(scenario_memories["memories"])
        }
    
    def print_roleplay_memory_stats(self, user_id: str):
        """打印角色扮演记忆统计信息"""
        self.smm.print_roleplay_memory_stats(user_id)
    
    def print_character_profile(self, user_id: str):
        """打印角色档案摘要"""
        profile = self.get_roleplay_profile(user_id)
        patterns = self.get_behavioral_patterns(user_id)
        scenarios = self.get_preferred_scenarios(user_id)
        
        print("🎭 角色档案摘要 ===")
        print(f"用户ID: {user_id}")
        print(f"身份特征: {profile['total_traits']} 项")
        print(f"行为模式: {patterns['pattern_count']} 种") 
        print(f"场景偏好: {scenarios['scenario_count']} 类")
        
        # 显示关键特征
        if profile['profile_memories']['memories']:
            print("\n🔑 关键身份特征:")
            for memory in profile['profile_memories']['memories'][:3]:
                metadata = memory.get('metadata', {})
                print(f"  • {memory['memory']} [重要性: {metadata.get('importance', 'unknown')}]")
        
        if patterns['behavioral_patterns']['memories']:
            print("\n🔄 行为模式:")
            for memory in patterns['behavioral_patterns']['memories'][:2]:
                print(f"  • {memory['memory']}")
    
    def print_memory_stats(self, user_id: str):
        """打印记忆统计信息"""
        stats = self.get_memory_stats(user_id)
        
        print("=== 记忆统计信息 ===")
        print(f"总记忆数量: {stats['total_memories']}")
        print(f"活跃记忆: {stats['active_memories']}")
        print(f"已删除记忆: {stats['deleted_memories']}")
        print()
        
        print("按重要性分布:")
        for importance, count in stats['by_importance'].items():
            print(f"  {importance}: {count}")
    
    def print_performance_stats(self):
        """打印性能统计信息"""
        print("=== 性能统计信息 ===")
        performance_monitor.print_performance_summary()
    
    def print_search_results(self, results: Dict[str, Any], title: str = "搜索结果"):
        """打印搜索结果"""
        self.smm.print_results(results, title)

    def force_delete_memory(self, search_query: str, user_id: str) -> int:
        """
        强制删除 - 不进行相关性检查，直接删除所有匹配项
        """
        print(f"💥 强制删除: {search_query}")
        
        results = self.smm.search_smart(search_query, user_id, exclude_deleted=False)
        
        deleted_count = 0
        for item in results['results']:
            # 不检查相关性，直接删除所有搜索结果
            if self.smm._execute_deletion(item, user_id):
                deleted_count += 1
        
        print(f"💥 强制删除完成: {deleted_count} 条记忆")
        return deleted_count

    def bulk_delete_by_category(self, category: str, user_id: str, 
                            importance_filter: Optional[str] = None) -> int:
        """
        按分类批量删除
        """
        print(f"🗂️ 按分类批量删除: {category}")
        
        category_results = self.search_by_category(category, user_id)
        deleted_count = 0
        
        for item in category_results['results']:
            # 可选的重要性过滤
            if importance_filter:
                metadata = item.get('metadata') or {}
                if metadata.get('importance') != importance_filter:
                    continue
                    
            if self.smm._execute_deletion(item, user_id):
                deleted_count += 1
        
        print(f"🗂️ 分类删除完成: {deleted_count} 条 {category} 记忆")
        return deleted_count

# 向后兼容的别名
Mem0App = RoleplayMem0App


if __name__ == "__main__":
    
    # 运行演示
    run_roleplay_demo()