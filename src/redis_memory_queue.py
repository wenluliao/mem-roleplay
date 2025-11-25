"""
Redis内存队列实现 - 用于异步处理角色扮演记忆
"""
import redis
import json
import threading
import time
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class RedisMemoryQueue:
    """Redis内存队列，用于异步处理角色扮演记忆"""
    
    def __init__(self, memory_manager, redis_url: str = "redis://:dxz@2024@test-dxz-jifen-pub.redis.rds.aliyuncs.com:6379/15", 
                 queue_name: str = "roleplay_memory_queue"):
        """
        初始化Redis队列
        
        Args:
            memory_manager: 内存管理器实例
            redis_url: Redis连接URL
            queue_name: 队列名称
        """
        self.memory_manager = memory_manager
        self.queue_name = queue_name
        self.redis_client = redis.from_url(redis_url)
        self.processing_thread = None
        self.is_running = False
        
        # 测试Redis连接
        try:
            self.redis_client.ping()
            logger.info(f"Redis连接成功，队列名称: {queue_name}")
        except redis.ConnectionError as e:
            logger.error(f"Redis连接失败: {e}")
            raise
    
    def add_memories(self, facts: List[Dict[str, Any]], user_id: str) -> Dict[str, Any]:
        """
        添加记忆到队列
        
        Args:
            facts: 分类后的事实列表
            user_id: 用户ID
            
        Returns:
            队列状态信息
        """
        try:
            # 创建任务数据
            task_data = {
                "facts": facts,
                "user_id": user_id,
                "timestamp": time.time(),
                "task_id": f"{user_id}_{int(time.time()*1000)}",
                "type": "memory_storage"  # 标记为记忆存储任务
            }
            
            # 添加到Redis队列
            self.redis_client.rpush(self.queue_name, json.dumps(task_data))
            
            # 获取队列长度
            queue_length = self.redis_client.llen(self.queue_name)
            
            logger.info(f"成功添加记忆任务到队列，用户: {user_id}, 任务数: {len(facts)}, 队列长度: {queue_length}")
            
            return {
                "status": "queued",
                "task_id": task_data["task_id"],
                "queue_length": queue_length,
                "facts_count": len(facts)
            }
            
        except Exception as e:
            logger.error(f"添加记忆到队列失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def add_conversation_task(self, messages: List[Dict[str, Any]], user_id: str) -> str:
        """
        添加对话处理任务到队列 - 用于异步处理完整的对话分类流程
        
        Args:
            messages: 对话消息列表
            user_id: 用户ID
            
        Returns:
            任务ID
        """
        try:
            # 创建任务数据
            task_data = {
                "messages": messages,
                "user_id": user_id,
                "timestamp": time.time(),
                "task_id": f"{user_id}_{int(time.time()*1000)}",
                "type": "conversation_processing"  # 标记为对话处理任务
            }
            
            # 添加到Redis队列
            self.redis_client.rpush(self.queue_name, json.dumps(task_data))
            
            # 获取队列长度
            queue_length = self.redis_client.llen(self.queue_name)
            
            logger.info(f"成功添加对话处理任务到队列，用户: {user_id}, 队列长度: {queue_length}")
            
            return task_data["task_id"]
            
        except Exception as e:
            logger.error(f"添加对话处理任务到队列失败: {e}")
            raise e
    
    def start_processing(self, batch_size: int = 10, sleep_interval: float = 1.0):
        """
        启动队列处理线程
        
        Args:
            batch_size: 批量处理大小
            sleep_interval: 处理间隔（秒）
        """
        if self.is_running:
            logger.warning("队列处理线程已在运行")
            return
        
        self.is_running = True
        self.processing_thread = threading.Thread(
            target=self._process_queue,
            args=(batch_size, sleep_interval),
            daemon=True
        )
        self.processing_thread.start()
        logger.info("队列处理线程已启动")
    
    def stop_processing(self):
        """停止队列处理线程"""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
            logger.info("队列处理线程已停止")
    
    def _process_queue(self, batch_size: int, sleep_interval: float):
        """
        处理队列中的任务
        
        Args:
            batch_size: 批量处理大小
            sleep_interval: 处理间隔
        """
        while self.is_running:
            try:
                # 批量获取任务
                tasks = []
                for _ in range(batch_size):
                    task_json = self.redis_client.lpop(self.queue_name)
                    if task_json:
                        task_data = json.loads(task_json)
                        tasks.append(task_data)
                    else:
                        break
                
                if tasks:
                    # 批量处理任务
                    self._process_batch(tasks)
                    logger.info(f"批量处理了 {len(tasks)} 个记忆任务")
                else:
                    # 队列为空，等待一段时间
                    time.sleep(sleep_interval)
                    
            except Exception as e:
                logger.error(f"处理队列时发生错误: {e}")
                time.sleep(sleep_interval)  # 出错后等待一段时间再继续
    
    def _process_batch(self, tasks: List[Dict[str, Any]]):
        """
        批量处理任务
        
        Args:
            tasks: 任务列表
        """
        try:
            for task in tasks:
                task_type = task.get("type", "memory_storage")
                user_id = task["user_id"]
                
                if task_type == "memory_storage":
                    # 处理记忆存储任务
                    facts = task.get("facts", [])
                    try:
                        result = self.memory_manager.add_roleplay_memories_batch(facts, user_id)
                        logger.info(f"用户 {user_id} 的记忆批量添加成功，数量: {len(facts)}")
                    except Exception as e:
                        logger.error(f"用户 {user_id} 的记忆添加失败: {e}")
                        
                elif task_type == "conversation_processing":
                    # 处理对话处理任务 - 完整的分类和存储流程
                    messages = task.get("messages", [])
                    try:
                        # 在后台线程中完成整个处理流程
                        print("🎭 开始角色扮演记忆分类...")
                        start_time = time.time()
                        
                        # 提取角色扮演事实
                        classified_facts = self.memory_manager._extract_roleplay_facts(messages)
                        
                        classification_time = time.time() - start_time
                        print(f"🎭 分类完成，耗时: {classification_time:.2f}s")
                        
                        # 存储分类结果
                        result = self.memory_manager.add_roleplay_memories_batch(classified_facts["facts"], user_id)
                        logger.info(f"用户 {user_id} 的对话处理完成，记忆数量: {len(classified_facts.get('facts', []))}")
                    except Exception as e:
                        logger.error(f"用户 {user_id} 的对话处理失败: {e}")
                        
        except Exception as e:
            logger.error(f"批量处理任务失败: {e}")
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        获取队列统计信息
        
        Returns:
            队列统计信息
        """
        try:
            queue_length = self.redis_client.llen(self.queue_name)
            return {
                "queue_name": self.queue_name,
                "queue_length": queue_length,
                "is_processing": self.is_running,
                "redis_connected": True
            }
        except Exception as e:
            return {
                "queue_name": self.queue_name,
                "queue_length": 0,
                "is_processing": False,
                "redis_connected": False,
                "error": str(e)
            }
    
    def clear_queue(self) -> bool:
        """
        清空队列
        
        Returns:
            是否成功
        """
        try:
            self.redis_client.delete(self.queue_name)
            logger.info("队列已清空")
            return True
        except Exception as e:
            logger.error(f"清空队列失败: {e}")
            return False