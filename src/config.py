"""
配置文件模块
处理应用配置和环境变量
"""

import os
from typing import Dict, Any

# 从环境变量读取配置，如果没有设置则使用默认值
openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1")
model_name = os.getenv("MODEL_NAME", "deepseek-ai/DeepSeek-V3.2-Exp")

class Config:
    """配置管理类"""
    
    def __init__(self):
        self._config = self._get_default_config()
        self._load_env_variables()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "llm": {
                "provider": "openai",
                "config": {
                    "model": model_name,
                    "temperature": 0.2,
                    "max_tokens": 2000,
                    "openai_base_url": openai_base_url
                }
            },
            "embedder": {
                "provider": "ollama",
                "config": {
                    "model": os.getenv("EMBEDDER_MODEL", "qwen3-embedding:0.6b"),
                    "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                }
            },
            "reranker": {
                "provider": "llm_reranker",
                "config": {
                    "llm": {
                        "provider": "openai",
                        "config": {
                            "model": "THUDM/GLM-4-9B-0414",
                            "api_key": os.getenv("OPENAI_API_KEY"),
                            "openai_base_url": openai_base_url
                        }
                    },
                    "model": "THUDM/GLM-4-9B-0414",
                    "top_k": 5
                }
            },
            # "embedder": {
            #     "provider": "openai",
            #     "config": {
            #         "model": os.getenv("EMBEDDER_MODEL", "Qwen/Qwen3-Embedding-8B"),
            #         "openai_base_url": openai_base_url
            #     }
            # },
            # "reranker": {
            #     "provider": "llm_reranker",
            #     "config": {
            #         "llm": {
            #             "provider": "ollama",
            #             "config": {
            #                 "model": "dengcao/Qwen3-Reranker-0.6B:F16",
            #                 "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            #             }
            #         }
            #     }
            # },
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "collection_name": os.getenv("COLLECTION_NAME", "test"),
                    "path": os.getenv("VECTOR_STORE_PATH", "db")
                }
            }
        }
    
    def _load_env_variables(self):
        """加载环境变量"""
        # OpenAI API Key
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self._config["llm"]["config"]["api_key"] = openai_key
        
        # Ollama 配置
        ollama_url = os.getenv("OLLAMA_BASE_URL")
        if ollama_url:
            self._config["embedder"]["config"]["ollama_base_url"] = ollama_url
            if "reranker" in self._config and "config" in self._config["reranker"]:
                self._config["reranker"]["config"]["llm"]["config"]["ollama_base_url"] = ollama_url
    
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._config
    
    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM配置"""
        return self._config["llm"]
    
    def get_embedder_config(self) -> Dict[str, Any]:
        """获取嵌入器配置"""
        return self._config["embedder"]
    
    def get_reranker_config(self) -> Dict[str, Any]:
        """获取重排器配置"""
        return self._config["reranker"]
    
    def get_vector_store_config(self) -> Dict[str, Any]:
        """获取向量存储配置"""
        return self._config["vector_store"]
    
    def update_config(self, section: str, key: str, value: Any):
        """更新配置"""
        if section in self._config:
            if isinstance(self._config[section], dict):
                self._config[section][key] = value
            else:
                raise ValueError(f"配置项 {section} 不是字典类型")
        else:
            raise ValueError(f"配置项 {section} 不存在")


# 全局配置实例
config = Config()