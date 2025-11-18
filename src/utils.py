"""
工具函数模块
包含各种辅助函数和工具类
"""

import re
import json
import datetime
import time
import logging
from datetime import timedelta
from typing import Dict, Any, List, Optional, Tuple, Callable
from difflib import SequenceMatcher
from functools import wraps

import chromadb
from openai import OpenAI


class LLMLogger:
    """LLM调用日志记录器"""
    
    def __init__(self, log_file: str = "llm_logs.jsonl"):
        """
        初始化LLM日志记录器
        
        Args:
            log_file: 日志文件路径
        """
        self.log_file = log_file
        self.logger = logging.getLogger(__name__)
        
        # 设置日志格式
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def log_request(self, model: str, messages: List[Dict], function_call: Optional[Dict] = None):
        """
        记录LLM请求
        
        Args:
            model: 模型名称
            messages: 消息列表
            function_call: 函数调用信息
        """
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "request",
            "model": model,
            "messages": messages,
            "function_call": function_call
        }
        
        self._write_log(log_entry)
        self.logger.info(f"LLM请求 - 模型: {model}, 消息数量: {len(messages)}")
    
    def log_response(self, model: str, response: str, usage: Any = None, 
                response_time: Optional[float] = None):
        """
        记录LLM响应 - 彻底修复序列化问题
        """
        # 彻底处理usage对象的序列化
        serializable_usage = None
        if usage is not None:
            try:
                # 方法1: 如果是OpenAI的Usage对象
                if hasattr(usage, 'prompt_tokens'):
                    serializable_usage = {
                        'prompt_tokens': usage.prompt_tokens,
                        'completion_tokens': usage.completion_tokens,
                        'total_tokens': usage.total_tokens
                    }
                # 方法2: 如果是字典
                elif isinstance(usage, dict):
                    serializable_usage = usage
                # 方法3: 其他情况转换为字符串
                else:
                    serializable_usage = str(usage)
            except Exception as e:
                # 如果所有方法都失败，记录错误但继续执行
                serializable_usage = f"serialization_error: {str(e)}"
                self.logger.warning(f"Usage序列化失败: {e}")
        
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "response",
            "model": model,
            "response": response,
            "usage": serializable_usage,
            "response_time": response_time
        }
        
        try:
            self._write_log(log_entry)
            self.logger.info(f"LLM响应 - 模型: {model}, 响应长度: {len(response)}, 耗时: {response_time:.2f}s")
        except Exception as e:
            # 即使日志写入失败，也不影响主流程
            self.logger.error(f"日志写入失败: {e}")
    
    def log_error(self, model: str, error: str, request_data: Optional[Dict] = None):
        """
        记录LLM错误
        
        Args:
            model: 模型名称
            error: 错误信息
            request_data: 请求数据
        """
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "error",
            "model": model,
            "error": error,
            "request_data": request_data
        }
        
        self._write_log(log_entry)
        self.logger.error(f"LLM错误 - 模型: {model}, 错误: {error}")
    
    def _write_log(self, log_entry: Dict[str, Any]):
        """
        写入日志到文件
        
        Args:
            log_entry: 日志条目
        """
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            self.logger.error(f"写入LLM日志失败: {e}")
    
    @staticmethod
    def get_llm_logger():
        """获取全局LLM日志记录器实例"""
        if not hasattr(LLMLogger, '_instance'):
            LLMLogger._instance = LLMLogger()
        return LLMLogger._instance


def log_llm_call(func: Callable) -> Callable:
    """
    LLM调用日志装饰器
    
    Args:
        func: 要装饰的LLM调用函数
        
    Returns:
        包装后的函数
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = LLMLogger.get_llm_logger()
        
        # 提取请求信息
        model = kwargs.get('model', 'unknown')
        messages = kwargs.get('messages', [])
        
        # 记录请求
        logger.log_request(model, messages)
        
        start_time = time.time()
        try:
            # 执行LLM调用
            response = func(*args, **kwargs)
            response_time = time.time() - start_time
            
            # 记录响应
            if hasattr(response, 'choices') and response.choices:
                response_content = response.choices[0].message.content
                usage = getattr(response, 'usage', None)
                logger.log_response(model, response_content, usage, response_time)
            
            return response
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.log_error(model, str(e), {
                'messages': messages,
                'model': model,
                'response_time': response_time
            })
            raise
    
    return wrapper


class LoggingOpenAIClient:
    """带日志记录的OpenAI客户端包装器"""
    
    def __init__(self, client: OpenAI):
        """
        初始化包装器
        
        Args:
            client: 原始的OpenAI客户端
        """
        self._client = client
        self._logger = LLMLogger.get_llm_logger()
    
    @log_llm_call
    def chat_completions_create(self, *args, **kwargs):
        """
        包装chat.completions.create方法
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            LLM响应
        """
        return self._client.chat.completions.create(*args, **kwargs)
    
    def __getattr__(self, name):
        """
        转发其他属性到原始客户端
        
        Args:
            name: 属性名
            
        Returns:
            属性值
        """
        return getattr(self._client, name)


class LLMLoggingMiddleware:
    """LLM日志记录中间件"""
    
    def __init__(self, enable_logging: bool = True):
        """
        初始化中间件
        
        Args:
            enable_logging: 是否启用日志记录
        """
        self.enable_logging = enable_logging
        self.logger = LLMLogger.get_llm_logger()
    
    def log_llm_request(self, provider: str, model: str, messages: List[Dict], 
                       function_call: Optional[Dict] = None):
        """
        记录LLM请求
        
        Args:
            provider: 服务提供商（openai/ollama等）
            model: 模型名称
            messages: 消息列表
            function_call: 函数调用信息
        """
        if not self.enable_logging:
            return
            
        self.logger.log_request(model, messages, function_call)
    
    def log_llm_response(self, provider: str, model: str, response: str, 
                        usage: Optional[Dict] = None, response_time: Optional[float] = None):
        """
        记录LLM响应
        
        Args:
            provider: 服务提供商
            model: 模型名称
            response: 响应内容
            usage: token使用情况
            response_time: 响应时间
        """
        if not self.enable_logging:
            return
            
        self.logger.log_response(model, response, usage, response_time)
    
    def log_llm_error(self, provider: str, model: str, error: str, 
                     request_data: Optional[Dict] = None):
        """
        记录LLM错误
        
        Args:
            provider: 服务提供商
            model: 模型名称
            error: 错误信息
            request_data: 请求数据
        """
        if not self.enable_logging:
            return
            
        self.logger.log_error(model, error, request_data)
    
    @staticmethod
    def get_middleware():
        """获取全局中间件实例"""
        if not hasattr(LLMLoggingMiddleware, '_instance'):
            LLMLoggingMiddleware._instance = LLMLoggingMiddleware()
        return LLMLoggingMiddleware._instance


class PerformanceMonitor:
    """性能监控类"""
    
    _performance_stats = {}
    
    @staticmethod
    def timeit(func: Callable) -> Callable:
        """
        性能监控装饰器
        
        Args:
            func: 要监控的函数
            
        Returns:
            包装后的函数
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            # 记录执行时间
            execution_time = end_time - start_time
            func_name = func.__name__
            
            # 更新统计信息
            if func_name not in PerformanceMonitor._performance_stats:
                PerformanceMonitor._performance_stats[func_name] = {
                    'total_calls': 0,
                    'total_time': 0.0,
                    'min_time': float('inf'),
                    'max_time': 0.0,
                    'last_execution': 0.0
                }
            
            stats = PerformanceMonitor._performance_stats[func_name]
            stats['total_calls'] += 1
            stats['total_time'] += execution_time
            stats['min_time'] = min(stats['min_time'], execution_time)
            stats['max_time'] = max(stats['max_time'], execution_time)
            stats['last_execution'] = execution_time
            
            # 打印耗时信息（如果超过阈值）
            threshold = 0.1  # 100毫秒
            if execution_time > threshold:
                print(f"⏱️  {func_name} 耗时: {execution_time:.3f}s")
            
            return result
        
        return wrapper
    
    @staticmethod
    def get_performance_stats() -> Dict[str, Any]:
        """获取性能统计信息"""
        return PerformanceMonitor._performance_stats.copy()
    
    @staticmethod
    def print_performance_summary():
        """打印性能摘要"""
        if not PerformanceMonitor._performance_stats:
            print("暂无性能统计数据")
            return
        
        print("\n📊 性能统计摘要:")
        print("-" * 80)
        print(f"{'函数名':<30} {'调用次数':<8} {'总耗时(s)':<10} {'平均耗时(s)':<12} {'最慢(s)':<10}")
        print("-" * 80)
        
        for func_name, stats in PerformanceMonitor._performance_stats.items():
            avg_time = stats['total_time'] / stats['total_calls'] if stats['total_calls'] > 0 else 0
            print(f"{func_name:<30} {stats['total_calls']:<8} {stats['total_time']:<10.3f} {avg_time:<12.3f} {stats['max_time']:<10.3f}")
        
        print("-" * 80)


class TextUtils:
    """文本处理工具类"""
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """计算两个文本的相似度（简单版本）"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    @staticmethod
    def calculate_relevance(memory_content: str, query: str) -> float:
        """计算记忆内容与查询的相关性"""
        # 简单的文本匹配算法
        memory_lower = memory_content.lower()
        query_lower = query.lower()
        
        # 检查完全包含
        if query_lower in memory_lower:
            return 1.0
        
        # 检查关键词匹配
        query_words = set(query_lower.split())
        memory_words = set(memory_lower.split())
        
        common_words = query_words & memory_words
        if not query_words:
            return 0.0
        
        return len(common_words) / len(query_words)
    
    @staticmethod
    def extract_important_points(messages: List[Dict[str, str]], user_id: str) -> List[Dict[str, Any]]:
        """从对话中提取重要信息（基于简单规则）"""
        important_points = []
        high_importance_words = ["过敏", "生日", "疾病", "密码", "账号", "讨厌", "害怕", "恐高"]
        medium_importance_words = ["喜欢", "不喜欢", "习惯", "经常", "一直", "爱看", "爱玩"]
        
        for msg in messages:
            if msg["role"] == "user":
                content = msg["content"]
                
                # 检查高重要性关键词
                if any(word in content for word in high_importance_words):
                    important_points.append({
                        "content": msg["content"],
                        "importance": "high",
                        "type": "preference"
                    })
                # 检查中重要性关键词  
                elif any(word in content for word in medium_importance_words):
                    important_points.append({
                        "content": msg["content"], 
                        "importance": "medium",
                        "type": "preference"
                    })
        
        return important_points
    
    @staticmethod
    def classify_memory_content(content: str, user_id: str) -> Dict[str, Any]:
        """智能分类记忆内容
        
        分类类型：
        - event: 事件（具体发生的事件）
        - profile: 用户档案（个人基本信息）
        - interaction: 互动交流（对话交流内容）
        - behavioral_patterns: 互动模式（行为习惯）
        - internal_monologue: 内心独白（用户内心想法）
        - interaction_context: 交互上下文（对话背景）
        - roleplay_scenarios: 角色扮演场景（角色设定）
        - general: 一般信息（无法分类的默认类型）
        
        Args:
            content: 记忆内容
            user_id: 用户ID
            
        Returns:
            分类结果字典
        """
        # 基于关键词的简单分类（在实际应用中可以使用LLM进行智能分类）
        content_lower = content.lower()
        
        # 事件分类关键词
        event_keywords = ["昨天", "今天", "明天", "上周", "下周", "去年", "明年", 
                         "发生", "事件", "经历", "遇到", "碰到", "遭遇"]
        
        # 用户档案关键词
        profile_keywords = ["姓名", "年龄", "性别", "生日", "地址", "电话", "邮箱", 
                           "职业", "工作", "学校", "专业", "身高", "体重"]
        
        # 互动交流关键词
        interaction_keywords = ["说", "告诉", "问", "回答", "讨论", "聊天", "对话", 
                               "交流", "沟通", "分享", "表达"]
        
        # 互动模式关键词
        behavioral_patterns_keywords = ["习惯", "经常", "总是", "通常", "一般", "喜欢", 
                                       "不喜欢", "偏好", "讨厌", "害怕", "担心"]
        
        # 内心独白关键词
        internal_monologue_keywords = ["觉得", "认为", "感觉", "想法", "思考", "考虑", 
                                     "希望", "想要", "打算", "计划", "梦想"]
        
        # 交互上下文关键词
        interaction_context_keywords = ["因为", "所以", "但是", "然而", "虽然", "如果", 
                                       "那么", "之前", "之后", "同时", "另外"]
        
        # 角色扮演场景关键词
        roleplay_scenarios_keywords = ["角色", "扮演", "设定", "场景", "故事", "剧情", 
                                     "人物", "角色", "身份", "背景", "世界观"]
        
        # 分类逻辑
        category_scores = {
            "event": sum(1 for keyword in event_keywords if keyword in content_lower),
            "profile": sum(1 for keyword in profile_keywords if keyword in content_lower),
            "interaction": sum(1 for keyword in interaction_keywords if keyword in content_lower),
            "behavioral_patterns": sum(1 for keyword in behavioral_patterns_keywords if keyword in content_lower),
            "internal_monologue": sum(1 for keyword in internal_monologue_keywords if keyword in content_lower),
            "interaction_context": sum(1 for keyword in interaction_context_keywords if keyword in content_lower),
            "roleplay_scenarios": sum(1 for keyword in roleplay_scenarios_keywords if keyword in content_lower),
        }
        
        # 找到最高分的分类
        max_score = max(category_scores.values())
        if max_score > 0:
            # 找到所有最高分的分类
            top_categories = [cat for cat, score in category_scores.items() if score == max_score]
            # 如果有多个相同分数的分类，选择第一个
            category = top_categories[0]
        else:
            category = "general"
        
        # 计算分类置信度
        total_keywords = sum(category_scores.values())
        confidence = max_score / total_keywords if total_keywords > 0 else 0.0
        
        return {
            "category": category,
            "confidence": confidence,
            "category_scores": category_scores
        }
    
    @staticmethod
    def merge_memory_contents(memories: List[Dict[str, Any]]) -> str:
        """合并多个记忆内容"""
        # 简单的合并策略：取最长的那个
        return max(memories, key=lambda x: len(x['memory']))['memory']


class MetadataUtils:
    """元数据处理工具类"""
    
    @staticmethod
    def safe_get_metadata(item: Dict[str, Any], key: str, default: Any = None) -> Any:
        """安全获取metadata中的值"""
        metadata = item.get('metadata') or {}
        return metadata.get(key, default)
    
    @staticmethod
    def create_memory_metadata(
        importance: str = "low",
        memory_type: str = "short_term",
        category: str = "general",
        auto_tagged: bool = False,
        ttl_days: Optional[int] = None,
        classification_confidence: float = 0.0
    ) -> Dict[str, Any]:
        """创建标准化的记忆元数据"""
        metadata = {
            "importance": importance,
            "memory_type": memory_type,
            "category": category,
            "auto_tagged": auto_tagged,
            "created_at": datetime.datetime.now().isoformat(),
            "version": 1,  # 初始版本
            "classification_confidence": classification_confidence
        }
        
        # 设置过期时间（如果是短期记忆）
        if ttl_days and importance == "low":
            metadata["expires_at"] = (
                datetime.datetime.now() + timedelta(days=ttl_days)
            ).isoformat()
        
        return metadata
    
    @staticmethod
    def create_update_metadata(old_metadata: Dict[str, Any], new_content: str) -> Dict[str, Any]:
        """创建更新后的元数据"""
        new_metadata = old_metadata.copy()
        new_metadata.update({
            "updated_at": datetime.datetime.now().isoformat(),
            "version": old_metadata.get('version', 1) + 1,
            "previous_version": old_metadata.get('id')  # 链接到旧版本
        })
        return new_metadata
    
    @staticmethod
    def create_deletion_metadata(old_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """创建删除标记的元数据"""
        new_metadata = old_metadata.copy()
        new_metadata.update({
            "deleted": True,
            "deleted_at": datetime.datetime.now().isoformat(),
            "deleted_reason": "user_request"
        })
        return new_metadata
    
    @staticmethod
    def create_merge_metadata(old_metadata: Dict[str, Any], merged_into: str) -> Dict[str, Any]:
        """创建合并标记的元数据"""
        new_metadata = old_metadata.copy()
        new_metadata.update({
            "merged": True,
            "merged_at": datetime.datetime.now().isoformat(),
            "merged_into": merged_into
        })
        return new_metadata


class ValidationUtils:
    """验证工具类"""
    
    @staticmethod
    def is_relevant_for_update(memory_content: str, search_query: str) -> bool:
        """判断记忆是否真的与搜索查询相关"""
        # 简单的相关性检查，可以根据需要扩展
        query_words = set(search_query.lower().split())
        memory_words = set(memory_content.lower().split())
        
        # 如果有共同的关键词，认为是相关的
        common_words = query_words & memory_words
        return len(common_words) > 0
    
    @staticmethod
    def validate_user_id(user_id: str) -> bool:
        """验证用户ID格式"""
        if not user_id or not isinstance(user_id, str):
            return False
        # 简单的验证：不能为空且长度合理
        return len(user_id.strip()) > 0 and len(user_id) <= 100
    
    @staticmethod
    def validate_messages(messages: List[Dict[str, str]]) -> bool:
        """验证消息格式"""
        if not isinstance(messages, list):
            return False
        
        for msg in messages:
            if not isinstance(msg, dict):
                return False
            if "role" not in msg or "content" not in msg:
                return False
            if msg["role"] not in ["user", "assistant"]:
                return False
            if not isinstance(msg["content"], str):
                return False
        
        return True


# 全局工具实例
text_utils = TextUtils()
metadata_utils = MetadataUtils()
validation_utils = ValidationUtils()

# 创建性能监控实例
performance_monitor = PerformanceMonitor()

# 创建LLM日志记录中间件实例
llm_logging_middleware = LLMLoggingMiddleware()


def setup_llm_logging():
    """设置LLM日志记录"""
    try:
        # 尝试导入OpenAI库来拦截客户端创建
        from openai import OpenAI
        
        # 保存原始OpenAI类
        original_openai_init = OpenAI.__init__
        
        def logged_openai_init(self, *args, **kwargs):
            """带日志记录的OpenAI客户端初始化"""
            # 记录配置信息
            print("🔧 OpenAI客户端初始化参数:")
            base_url = kwargs.get('base_url', '默认(api.openai.com)')
            print(f"   - base_url: {base_url}")
            api_key_status = '已设置' if kwargs.get('api_key') else '未设置'
            print(f"   - api_key: {api_key_status}")
            
            # 先调用原始初始化
            original_openai_init(self, *args, **kwargs)
            
            # 保存原始chat.completions.create方法
            original_chat_create = self.chat.completions.create
            
            def logged_chat_create(*args, **kwargs):
                """带日志记录的chat.completions.create方法"""
                logger = LLMLogger.get_llm_logger()
                
                # 提取请求信息
                model = kwargs.get('model', 'unknown')
                messages = kwargs.get('messages', [])
                
                # 记录请求
                logger.log_request(model, messages)
                print(f"📤 LLM请求记录: {model} - {len(messages)}条消息")
                
                start_time = time.time()
                try:
                    # 执行原始调用
                    response = original_chat_create(*args, **kwargs)
                    response_time = time.time() - start_time
                    
                    # 记录响应
                    if hasattr(response, 'choices') and response.choices:
                        response_content = response.choices[0].message.content
                        usage = getattr(response, 'usage', None)
                        logger.log_response(model, response_content, usage, response_time)
                        print(f"📥 LLM响应记录: {model} - 耗时: {response_time:.2f}s")
                    
                    return response
                    
                except Exception as e:
                    response_time = time.time() - start_time
                    # 检查错误信息中是否包含URL信息
                    error_str = str(e)
                    if 'https://' in error_str:
                        # 提取URL信息
                        import re
                        urls = re.findall(r'https://[^\s\']+', error_str)
                        if urls:
                            print(f"🌐 实际调用URL: {urls[0]}")
                    
                    logger.log_error(model, error_str, {
                        'messages': messages,
                        'model': model,
                        'response_time': response_time
                    })
                    print(f"❌ LLM异常记录: {error_str}")
                    raise
            
            # 应用猴子补丁到chat.completions.create
            self.chat.completions.create = logged_chat_create
            print(f"✅ OpenAI客户端日志记录已启用")
        
        # 应用猴子补丁到OpenAI类
        OpenAI.__init__ = logged_openai_init
        print("✅ LLM日志记录已启用")
        
    except ImportError:
        print("⚠️ 警告: 无法导入OpenAI库，LLM日志记录未启用")
    except Exception as e:
        print(f"❌ 设置LLM日志记录时出错: {e}")