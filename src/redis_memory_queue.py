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
                "task_id": f"{user_id}_{int(time.time()*1000)}"
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
            # 按用户分组处理
            user_tasks = {}
            for task in tasks:
                user_id = task["user_id"]
                if user_id not in user_tasks:
                    user_tasks[user_id] = []
                user_tasks[user_id].extend(task["facts"])
            
            # 为每个用户批量添加记忆
            for user_id, facts in user_tasks.items():
                try:
                    # 调用同步方法批量添加记忆
                    result = self.memory_manager.add_roleplay_memories_batch(facts, user_id)
                    logger.info(f"用户 {user_id} 的记忆批量添加成功，数量: {len(facts)}")
                except Exception as e:
                    logger.error(f"用户 {user_id} 的记忆添加失败: {e}")
                    
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