"""
Mem0AI Web服务 - 提供HTTP API接口用于角色扮演记忆管理
"""
import os
import logging
from typing import Dict, Any, List, Optional  # 添加 Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from contextlib import asynccontextmanager

from .app import Mem0App
from .roleplay_smart_memory_manager import RoleplaySmartMemoryManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    logger.info("Mem0AI Web服务正在启动...")
    get_mem0_app()
    yield
    # 关闭时执行
    logger.info("Mem0AI Web服务正在关闭...")
    global roleplay_manager
    if roleplay_manager and hasattr(roleplay_manager, 'async_processor') and roleplay_manager.async_processor:
        roleplay_manager.async_processor.stop_processing()
        logger.info("异步队列处理已停止")

# 在创建 FastAPI 应用时使用 lifespan
app = FastAPI(
    title="Mem0AI角色扮演记忆服务",
    description="提供角色扮演对话记忆的HTTP API接口", 
    version="1.0.0",
    lifespan=lifespan  # 添加这行
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局应用实例
mem0_app = None
roleplay_manager = None


class ConversationRequest(BaseModel):
    """对话请求模型"""
    user_id: str
    dialogue: List[Dict[str, str]]
    use_async: bool = True


class MemorySearchRequest(BaseModel):
    """记忆搜索请求模型"""
    user_id: str
    query: str
    category: str = "all"
    limit: int = 10


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    service: str
    version: str
    queue_status: Dict[str, Any]


class AddMemoryResponse(BaseModel):
    """添加记忆响应模型"""
    status: str
    message: str
    task_id: Optional[str] = None  # 修复：改为 Optional
    queue_length: int = 0
    facts_count: int = 0


class SearchMemoryResponse(BaseModel):
    """搜索记忆响应模型"""
    status: str
    results: List[Dict[str, Any]]
    total_count: int


def get_mem0_app():
    """获取Mem0App实例"""
    global mem0_app, roleplay_manager
    
    if mem0_app is None:
        try:
            # 初始化应用
            mem0_app = Mem0App()
            
            # 初始化角色扮演记忆管理器（传递正确的memory_client）
            roleplay_manager = RoleplaySmartMemoryManager(
                memory_client=mem0_app.smm.memory,  # 关键修复
                use_async=True
            )
            
            # 启动异步队列处理
            if hasattr(roleplay_manager, 'async_processor') and roleplay_manager.async_processor:
                roleplay_manager.async_processor.start_processing()
                logger.info("异步队列处理已启动")
            
            logger.info("Mem0AI应用初始化完成")
            
        except Exception as e:
            logger.error(f"初始化Mem0AI应用失败: {e}")
            raise HTTPException(status_code=500, detail=f"服务初始化失败: {e}")
    
    return mem0_app


def get_roleplay_manager():
    """获取角色扮演记忆管理器实例"""
    global roleplay_manager
    
    if roleplay_manager is None:
        get_mem0_app()
    
    return roleplay_manager


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("Mem0AI Web服务正在启动...")
    get_mem0_app()


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    global roleplay_manager
    
    logger.info("Mem0AI Web服务正在关闭...")
    
    if roleplay_manager and hasattr(roleplay_manager, 'async_processor') and roleplay_manager.async_processor:
        roleplay_manager.async_processor.stop_processing()
        logger.info("异步队列处理已停止")


@app.get("/", response_model=HealthResponse)
async def health_check():
    """健康检查接口"""
    try:
        manager = get_roleplay_manager()
        queue_status = {}
        
        if hasattr(manager, 'async_processor') and manager.async_processor:
            queue_status = manager.async_processor.get_queue_stats()
        
        return HealthResponse(
            status="healthy",
            service="Mem0AI Roleplay Memory Service",
            version="1.0.0",
            queue_status=queue_status
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务异常: {e}")


@app.post("/api/v1/conversation/add", response_model=AddMemoryResponse)
async def add_conversation_memory(request: ConversationRequest):
    """添加对话记忆"""
    try:
        logger.info(f"收到对话记忆添加请求，用户: {request.user_id}, 对话轮次: {len(request.dialogue)}")
        
        manager = get_roleplay_manager()
        result = manager.add_conversation_with_roleplay_classification(
            request.dialogue,
            request.user_id
        )
        
        return AddMemoryResponse(
            status="success",
            message="对话记忆添加成功",
            task_id=result.get("task_id"),
            queue_length=result.get("queue_length", 0),
            facts_count=result.get("facts_count", 0)
        )
        
    except Exception as e:
        logger.error(f"添加对话记忆失败: {e}")
        raise HTTPException(status_code=500, detail=f"添加对话记忆失败: {e}")


@app.post("/api/v1/memory/search", response_model=SearchMemoryResponse)
async def search_memory(request: MemorySearchRequest):
    """搜索记忆"""
    try:
        logger.info(f"收到记忆搜索请求，用户: {request.user_id}, 查询: {request.query}")
        
        manager = get_roleplay_manager()
        results = manager.search_roleplay_memories(
            user_id=request.user_id,
            query=request.query,
            category=request.category if request.category != "all" else None,
            limit=request.limit
        )
        
        return SearchMemoryResponse(
            status="success",
            results=results,
            total_count=len(results)
        )
        
    except Exception as e:
        logger.error(f"搜索记忆失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索记忆失败: {e}")


@app.get("/api/v1/queue/status")
async def get_queue_status():
    """获取队列状态"""
    try:
        manager = get_roleplay_manager()
        if hasattr(manager, 'async_processor') and manager.async_processor:
            return manager.async_processor.get_queue_stats()
        else:
            return {"status": "async_processing_disabled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取队列状态失败: {e}")


@app.delete("/api/v1/queue/clear")
async def clear_queue():
    """清空队列"""
    try:
        manager = get_roleplay_manager()
        if hasattr(manager, 'async_processor') and manager.async_processor:
            success = manager.async_processor.clear_queue()
            return {"status": "success" if success else "failed"}
        else:
            return {"status": "async_processing_disabled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空队列失败: {e}")

def run_web_service(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """运行Web服务"""
    logger.info(f"启动Mem0AI Web服务: http://{host}:{port}")
    
    uvicorn.run(
        "src.web_service:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    run_web_service()