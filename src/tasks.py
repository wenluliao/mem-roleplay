# tasks.py
from celery import Celery
import json
import os
import time

# Celery配置 - 从环境变量读取Redis连接信息
redis_broker_url = os.getenv('CELERY_BROKER_URL', 'redis://:dxz@2024@test-dxz-jifen-pub.redis.rds.aliyuncs.com:6379/15')
redis_backend_url = os.getenv('CELERY_RESULT_BACKEND', 'redis://:dxz@2024@test-dxz-jifen-pub.redis.rds.aliyuncs.com:6379/15')

celery_app = Celery('memory_tasks', 
                    broker=redis_broker_url,
                    backend=redis_backend_url)

# Celery配置选项
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
)

@celery_app.task
def process_memory_batch_async(batch_data):
    """异步处理记忆批次"""
    try:
        # 动态导入以避免循环依赖
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))
        
        from app import Mem0App
        
        # 创建应用实例
        app = Mem0App(use_async=False)  # 避免递归异步
        facts_list = batch_data["facts"]
        user_id = batch_data["user_id"]
        
        # 使用记忆管理器处理批次
        result = app.memory_manager.add_roleplay_memories_batch(facts_list, user_id)
        
        return {
            "success": True,
            "processed_count": len(facts_list),
            "added_count": result["added_count"],
            "batch_id": batch_data.get("batch_id")
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return {
            "success": False,
            "error": str(e),
            "error_details": error_details,
            "batch_id": batch_data.get("batch_id")
        }

# 在记忆管理器中调用
class AsyncMemoryManager:
    def add_memories_async(self, facts_list, user_id):
        """异步添加记忆"""
        batch_data = {
            "facts": facts_list,
            "user_id": user_id,
            "batch_id": f"batch_{int(time.time()*1000)}",
            "timestamp": time.time()
        }
        
        # 发送到Celery任务队列
        task = process_memory_batch_async.apply_async(args=[batch_data])
        
        print(f"📤 已提交异步任务: {task.id}")
        return task.id