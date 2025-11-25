"""
智能记忆管理器模块
核心的记忆管理功能
"""

import datetime
from typing import Dict, Any, List, Optional
from mem0 import Memory

from .config import config
from .utils import text_utils, metadata_utils, validation_utils, PerformanceMonitor

# 创建性能监控实例
performance_monitor = PerformanceMonitor()


class SmartMemoryManager:
    """智能记忆管理器"""
    
    def __init__(self, memory_client: Optional[Memory] = None):
        """
        初始化智能记忆管理器
        
        Args:
            memory_client: 可选的Memory客户端实例，如果为None则从配置创建
        """
        if memory_client is None:
            self.memory = Memory.from_config(config.get_config())
        else:
            self.memory = memory_client
            
        self.access_count = {}  # 记录记忆被访问次数
        self.memory_updates = {}  # 记录记忆更新历史
    
    @performance_monitor.timeit
    def add_conversation(self, messages: List[Dict[str, str]], user_id: str, 
                        conversation_context: Optional[Dict[str, Any]] = None,
                        enable_classification: bool = True,
                        skip_default_processing: bool = False) -> Dict[str, Any]:
        """
        添加对话并自动标记重要性和分类
        
        Args:
            messages: 对话消息列表
            user_id: 用户ID
            conversation_context: 对话上下文信息
            enable_classification: 是否启用智能分类
            
        Returns:
            添加结果
        """
        # 验证输入
        if not validation_utils.validate_messages(messages):
            raise ValueError("消息格式无效")
        if not validation_utils.validate_user_id(user_id):
            raise ValueError("用户ID格式无效")
        
        # 如果跳过默认处理，直接返回空结果
        if skip_default_processing:
            return {"results": [], "total_count": 0}

        # 先让Mem0处理原始对话
        result = self.memory.add(messages, user_id=user_id)
        
        # 额外提取重要信息单独存储
        # important_points = text_utils.extract_important_points(messages, user_id)
        # for point in important_points:
        #     if enable_classification:
        #         # 对重要信息进行智能分类
        #         classification_result = text_utils.classify_memory_content(point["content"], user_id)
        #         point["category"] = classification_result["category"]
        #         point["classification_confidence"] = classification_result["confidence"]
        #     self._add_with_importance(point, user_id)
        
        return result
    
    def _add_with_importance(self, point: Dict[str, Any], user_id: str, 
                           ttl_days: Optional[int] = None) -> Dict[str, Any]:
        """
        添加带重要性标记和分类的记忆
        
        Args:
            point: 重要信息点
            user_id: 用户ID
            ttl_days: 过期天数（仅对低重要性记忆有效）
            
        Returns:
            添加结果
        """
        metadata = metadata_utils.create_memory_metadata(
            importance=point["importance"],
            memory_type="long_term" if point["importance"] in ["high", "medium"] else "short_term",
            category=point.get("category", point.get("type", "general")),
            auto_tagged=True,
            ttl_days=ttl_days,
            classification_confidence=point.get("classification_confidence", 0.0)
        )
        
        return self.memory.add(point["content"], user_id=user_id, metadata=metadata)
    
    @performance_monitor.timeit
    def update_memory(self, search_query: str, new_content: str, user_id: str, 
                     importance: Optional[str] = None) -> int:
        """
        更新现有记忆
        
        Args:
            search_query: 搜索查询
            new_content: 新内容
            user_id: 用户ID
            importance: 新的重要性级别
            
        Returns:
            更新的记忆数量
        """
        print(f"正在搜索要更新的记忆: {search_query}")
        
        # 搜索相关记忆
        results = self.memory.search(search_query, user_id=user_id,rerank=False)
        
        updated_count = 0
        for item in results['results']:
            # 检查是否真的相关（避免误更新）
            if validation_utils.is_relevant_for_update(item['memory'], search_query):
                print(f"找到要更新的记忆: {item['memory']}")
                print(f"更新为: {new_content}")
                
                # 记录更新历史
                memory_id = item['id']
                if memory_id not in self.memory_updates:
                    self.memory_updates[memory_id] = []
                
                self.memory_updates[memory_id].append({
                    "old_content": item['memory'],
                    "new_content": new_content,
                    "updated_at": datetime.datetime.now().isoformat()
                })
                
                # 创建新的metadata
                old_metadata = item.get('metadata') or {}
                new_metadata = metadata_utils.create_update_metadata(old_metadata, new_content)
                
                # 如果指定了新的重要性，更新它
                if importance:
                    new_metadata["importance"] = importance
                
                # 添加更新后的记忆
                self.memory.add(new_content, user_id=user_id, metadata=new_metadata)
                updated_count += 1
        
        print(f"成功更新 {updated_count} 条记忆")
        return updated_count
    
    def delete_memory(self, search_query: str, user_id: str, 
                 confirm_threshold: float = 0.8) -> int:
        """
        直接删除记忆 - 不再犹豫
        """
        print(f"🗑️ 执行删除搜索: {search_query}")
        
        # 精确搜索目标记忆
        results = self.memory.search(search_query, user_id=user_id, limit=10, rerank=True)
        
        deleted_count = 0
        
        for item in results['results']:
            # 计算相关性，达到阈值就删
            relevance_score = text_utils.calculate_relevance(item['memory'], search_query)
            
            if relevance_score >= confirm_threshold:
                print(f"✅ 删除确认: {item['memory']} (相关性: {relevance_score:.2f})")
                
                # 直接执行删除
                if self._execute_deletion(item, user_id):
                    deleted_count += 1
        
        print(f"🎯 删除完成: {deleted_count} 条记忆")
        return deleted_count

    def _execute_deletion(self, memory_item: Dict[str, Any], user_id: str) -> bool:
        """执行实际删除操作"""
        try:
            memory_id = memory_item['id']
            memory_content = memory_item['memory']
            
            # 方法1: 如果mem0支持直接删除
            if hasattr(self.memory, 'delete') and callable(getattr(self.memory, 'delete')):
                result = self.memory.delete(memory_id, user_id=user_id)
                if result:
                    print(f"🔥 直接删除: {memory_content}")
                    return True
            
            # 方法2: 使用更新方式标记为已删除
            return self._hard_delete_mark(memory_item, user_id)
            
        except Exception as e:
            print(f"❌ 删除执行失败: {e}")
            return False

    def _hard_delete_mark(self, memory_item: Dict[str, Any], user_id: str) -> bool:
        """硬删除标记 - 让记忆在搜索中不可见"""
        try:
            # 创建明确的删除标记metadata
            deletion_metadata = {
                "deleted": True,
                "deleted_at": datetime.datetime.now().isoformat(),
                "deleted_reason": "user_request",
                "original_content": memory_item['memory'],  # 保留原内容用于审计
                "deletion_type": "hard_mark"
            }
            
            # 添加删除记录
            result = self.memory.add(
                f"[DELETED] {memory_item['memory']}", 
                user_id=user_id, 
                metadata=deletion_metadata
            )
            
            print(f"🔥 硬删除标记: {memory_item['memory']}")
            return True
            
        except Exception as e:
            print(f"❌ 硬删除标记失败: {e}")
            return False
    
    def _mark_as_deleted(self, memory_item: Dict[str, Any], user_id: str):
        """标记记忆为已删除（通过metadata）"""
        metadata = memory_item.get('metadata') or {}
        new_metadata = metadata_utils.create_deletion_metadata(metadata)
        
        # 添加删除标记的新记录
        self.memory.add(
            f"[已删除] {memory_item['memory']}", 
            user_id=user_id, 
            metadata=new_metadata
        )
    
    @performance_monitor.timeit
    def cleanup_expired_memories(self, user_id: str) -> int:
        """
        清理过期记忆
        
        Args:
            user_id: 用户ID
            
        Returns:
            清理的记忆数量
        """
        print("正在清理过期记忆...")
        
        all_memories = self.get_all_memories(user_id)
        current_time = datetime.datetime.now()
        cleaned_count = 0
        
        for item in all_memories['results']:
            metadata = item.get('metadata') or {}
            expires_at = metadata.get('expires_at')
            
            if expires_at:
                try:
                    expire_time = datetime.datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    if current_time > expire_time:
                        print(f"清理过期记忆: {item['memory']}")
                        self._mark_as_deleted(item, user_id)
                        cleaned_count += 1
                except ValueError:
                    continue
        
        print(f"清理了 {cleaned_count} 条过期记忆")
        return cleaned_count
    
    @performance_monitor.timeit
    def merge_similar_memories(self, user_id: str, similarity_threshold: float = 0.7) -> int:
        """
        合并相似记忆
        
        Args:
            user_id: 用户ID
            similarity_threshold: 相似度阈值
            
        Returns:
            合并的记忆数量
        """
        print("正在合并相似记忆...")
        
        all_memories = self.get_all_memories(user_id)
        merged_count = 0
        
        # 简单的相似度检测和合并
        processed_ids = set()
        
        for i, item1 in enumerate(all_memories['results']):
            if item1['id'] in processed_ids:
                continue
                
            similar_memories = [item1]
            
            for j, item2 in enumerate(all_memories['results'][i+1:], i+1):
                if item2['id'] in processed_ids:
                    continue
                    
                similarity = text_utils.calculate_similarity(item1['memory'], item2['memory'])
                if similarity > similarity_threshold:
                    similar_memories.append(item2)
                    processed_ids.add(item2['id'])
            
            # 如果找到相似记忆，合并它们
            if len(similar_memories) > 1:
                merged_content = text_utils.merge_memory_contents(similar_memories)
                print(f"合并 {len(similar_memories)} 条相似记忆: {merged_content}")
                
                # 标记旧的为已合并
                for memory in similar_memories[1:]:  # 保留第一个
                    self._mark_as_merged(memory, user_id, merged_content)
                
                merged_count += len(similar_memories) - 1
        
        print(f"合并了 {merged_count} 条重复记忆")
        return merged_count
    
    def _mark_as_merged(self, memory_item: Dict[str, Any], user_id: str, merged_into: str):
        """标记记忆为已合并"""
        metadata = memory_item.get('metadata') or {}
        new_metadata = metadata_utils.create_merge_metadata(metadata, merged_into)
        
        self.memory.add(
            f"[已合并] {memory_item['memory']}", 
            user_id=user_id, 
            metadata=new_metadata
        )
    
    def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """
        获取记忆统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            统计信息字典
        """
        all_memories = self.get_all_memories(user_id)
        
        stats = {
            "total_memories": len(all_memories['results']),
            "by_importance": {"high": 0, "medium": 0, "low": 0},
            "by_type": {"long_term": 0, "short_term": 0},
            "active_memories": 0,
            "deleted_memories": 0
        }
        
        for item in all_memories['results']:
            metadata = item.get('metadata') or {}
            
            # 统计重要性
            importance = metadata.get('importance', 'low')
            stats["by_importance"][importance] = stats["by_importance"].get(importance, 0) + 1
            
            # 统计类型
            memory_type = metadata.get('memory_type', 'short_term')
            stats["by_type"][memory_type] = stats["by_type"].get(memory_type, 0) + 1
            
            # 统计活跃记忆
            if not metadata.get('deleted') and not metadata.get('merged'):
                stats["active_memories"] += 1
            
            # 统计已删除记忆
            if metadata.get('deleted'):
                stats["deleted_memories"] += 1
        
        return stats
    
    @performance_monitor.timeit
    def search_smart(self, query: str, user_id: str, 
                    category: Optional[str] = None,
                    agent_id: Optional[str] = None,
                    min_importance: Optional[str] = None, 
                    exclude_deleted: bool = None,
                    limit: int = 5) -> Dict[str, Any]:
        """
        智能搜索 - 自动排除已删除内容
        """
        filterQuery = {}
        if category:
            filterQuery['category'] = category
        # if agent_id:
        #     filterQuery['agent_id'] = agent_id
        
        results = self.memory.search(query, user_id=user_id,filters=filterQuery,limit=limit, rerank=False)
        
        # 严格过滤已删除的记忆
        if exclude_deleted:
            filtered_results = []
            for item in results['results']:
                metadata = item.get('metadata') or {}
                # 排除所有标记为删除的内容
                if not metadata.get('deleted', False):
                    # 同时排除以 [DELETED] 开头的内容
                    if not item['memory'].startswith('[DELETED]'):
                        filtered_results.append(item)
            
            results['results'] = filtered_results
            results['total_count'] = len(filtered_results)
        
        # 更新访问计数
        for item in results['results']:
            memory_id = item['id']
            self.access_count[memory_id] = self.access_count.get(memory_id, 0) + 1
            item['access_count'] = self.access_count[memory_id]
        
        # 过滤已删除的记忆
        if exclude_deleted:
            results['results'] = [
                item for item in results['results'] 
                if not metadata_utils.safe_get_metadata(item, 'deleted', False)
            ]
        
        # 重要性过滤
        if min_importance:
            importance_levels = {"high": 2, "medium": 1, "low": 0}
            min_level = importance_levels.get(min_importance, 0)
            
            filtered_results = []
            for item in results['results']:
                importance = metadata_utils.safe_get_metadata(item, 'importance', 'low')
                current_level = importance_levels.get(importance, 0)
                
                if current_level >= min_level:
                    filtered_results.append(item)
            
            results['results'] = filtered_results
        
        # 按访问次数排序
        results['results'].sort(key=lambda x: x.get('access_count', 0), reverse=True)
        
        return results
    
    def get_all_memories(self, user_id: str, limit: int = 50) -> Dict[str, Any]:
        """
        获取用户的所有记忆
        
        Args:
            user_id: 用户ID
            limit: 限制数量
            
        Returns:
            所有记忆结果
        """
        return self.memory.search("个人 信息 记忆", user_id=user_id, limit=limit)
    
    def get_important_memories(self, user_id: str, importance_level: str = "medium") -> Dict[str, Any]:
        """获取重要记忆 - 修复完整实现"""
        all_results = self.get_all_memories(user_id)
        
        importance_levels = {"high": 2, "medium": 1, "low": 0}
        min_level = importance_levels.get(importance_level, 0)
        
        filtered_results = []
        for item in all_results['results']:
            importance = metadata_utils.safe_get_metadata(item, 'importance', 'low')
            current_level = importance_levels.get(importance, 0)
            
            if current_level >= min_level:
                filtered_results.append(item)
        
        filtered_results.sort(key=lambda x: self.access_count.get(x['id'], 0), reverse=True)
        return {'results': filtered_results}
    
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
        print(f"正在搜索分类为 '{category}' 的记忆...")
        
        # 获取所有记忆
        all_memories = self.get_all_memories(user_id, limit=100)
        
        # 按分类过滤
        filtered_results = []
        for item in all_memories['results']:
            metadata = item.get('metadata') or {}
            item_category = metadata.get('category', 'general')
            confidence = metadata.get('classification_confidence', 0.0)
            
            if item_category == category and confidence >= min_confidence:
                filtered_results.append(item)
        
        return {
            'results': filtered_results,
            'total_count': len(filtered_results),
            'category': category,
            'min_confidence': min_confidence
        }
    
    def get_category_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        获取分类统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            分类统计信息
        """
        all_memories = self.get_all_memories(user_id, limit=200)
        
        category_stats = {}
        total_memories = len(all_memories['results'])
        
        for item in all_memories['results']:
            metadata = item.get('metadata') or {}
            category = metadata.get('category', 'general')
            
            if category not in category_stats:
                category_stats[category] = {
                    'count': 0,
                    'avg_confidence': 0.0,
                    'total_confidence': 0.0
                }
            
            category_stats[category]['count'] += 1
            confidence = metadata.get('classification_confidence', 0.0)
            category_stats[category]['total_confidence'] += confidence
        
        # 计算平均置信度
        for category, stats in category_stats.items():
            if stats['count'] > 0:
                stats['avg_confidence'] = stats['total_confidence'] / stats['count']
                stats['percentage'] = (stats['count'] / total_memories) * 100
        
        return {
            'total_memories': total_memories,
            'categories': category_stats,
            'category_count': len(category_stats)
        }
        all_results = self.get_all_memories(user_id)
        
        importance_levels = {"high": 2, "medium": 1, "low": 0}
        min_level = importance_levels.get(importance_level, 0)
        
        filtered_results = []
        for item in all_results['results']:
            importance = metadata_utils.safe_get_metadata(item, 'importance', 'low')
            current_level = importance_levels.get(importance, 0)
            
            if current_level >= min_level:
                filtered_results.append(item)
        
        filtered_results.sort(key=lambda x: self.access_count.get(x['id'], 0), reverse=True)
        return {'results': filtered_results}
    
    def get_frequently_accessed(self, user_id: str, min_count: int = 2) -> Dict[str, Any]:
        """
        获取经常被访问的记忆
        
        Args:
            user_id: 用户ID
            min_count: 最小访问次数
            
        Returns:
            频繁访问的记忆结果
        """
        all_memories = self.get_all_memories(user_id)
        
        frequent = []
        for item in all_memories['results']:
            if self.access_count.get(item['id'], 0) >= min_count:
                frequent.append(item)
        
        frequent.sort(key=lambda x: self.access_count[x['id']], reverse=True)
        return {'results': frequent}
    
    def print_results(self, results: Dict[str, Any], title: str = "搜索结果"):
        """安全打印结果"""
        print(f"=== {title} ===")
        if not results['results']:
            print("没有找到相关记忆")
            return
            
        for i, item in enumerate(results['results'], 1):
            importance = metadata_utils.safe_get_metadata(item, 'importance', 'low')
            access_count = item.get('access_count', self.access_count.get(item['id'], 0))
            memory_content = item['memory']
            
            # 标记已删除或已合并的记忆
            status = ""
            if metadata_utils.safe_get_metadata(item, 'deleted', False):
                status = " [已删除]"
            elif metadata_utils.safe_get_metadata(item, 'merged', False):
                status = " [已合并]"
            
            print(f"{i}. {memory_content}{status}")
            print(f"   [重要性:{importance}, 访问次数:{access_count}, 分数:{item['score']:.3f}]")
            print()

    @performance_monitor.timeit
    def cleanup_memories(self, user_id: str) -> Dict[str, int]:
        """
        强力清理记忆
        """
        print("🧹 执行记忆清理...")
        
        # 1. 清理过期记忆
        expired_count = self.cleanup_expired_memories(user_id)
        
        # 2. 合并相似记忆  
        merged_count = self.merge_similar_memories(user_id)
        
        # 3. 清理低价值记忆（新增）
        low_value_count = self.cleanup_low_value_memories(user_id)
        
        return {
            "expired_cleaned": expired_count,
            "similar_merged": merged_count,
            "low_value_cleaned": low_value_count
        }

    def cleanup_low_value_memories(self, user_id: str, min_importance: str = "low") -> int:
        """清理低重要性且很少访问的记忆"""
        all_memories = self.get_all_memories(user_id)
        cleaned_count = 0
        
        for item in all_memories['results']:
            metadata = item.get('metadata') or {}
            importance = metadata.get('importance', 'low')
            access_count = self.access_count.get(item['id'], 0)
            
            # 低重要性 + 很少访问 + 不是最近创建的
            if (importance == 'low' and access_count <= 1 and 
                not metadata.get('deleted', False)):
                
                if self._execute_deletion(item, user_id):
                    cleaned_count += 1
        
        print(f"🧹 清理低价值记忆: {cleaned_count} 条")
        return cleaned_count