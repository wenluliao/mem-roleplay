# 🎭 Mem-Roleplay 角色扮演智能记忆系统

专为角色扮演场景优化的智能记忆管理系统，提供对话记忆管理、角色档案构建、行为模式分析等高级功能，支持异步处理和Web服务接口。

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Redis](https://img.shields.io/badge/Queue-Redis-DC382D.svg)](https://redis.io/)

## ✨ 核心特性

### 🎯 角色扮演专用优化
- **智能记忆分类**: 基于LLM自动识别和分类角色扮演相关记忆
- **角色档案构建**: 自动构建用户角色档案和行为模式
- **场景上下文管理**: 维护角色扮演的完整上下文信息
- **冲突检测机制**: 智能识别重复或冲突记忆，支持更新而非覆盖
- **异步处理支持**: 支持Redis队列异步处理对话记忆

### 🔧 技术特性
- **LLM支持**: 支持DeepSeek V3.2等LLM后端
- **智能向量检索**: 基于语义的智能记忆搜索和匹配
- **异步任务队列**: 基于Redis的异步处理架构
- **Web服务接口**: 提供RESTful API接口，支持HTTP调用
- **模块化架构**: 清晰的代码结构，易于扩展和维护

### 📊 记忆管理
- **7种记忆分类**: profile、behavioral_patterns、internal_monologue等
- **重要性分级**: 高、中、低三级重要性标记
- **生命周期管理**: 支持记忆更新、删除、清理、合并
- **访问统计**: 详细的记忆访问和使用统计

## 🚀 快速开始

### 系统要求
- Python 3.8+
- Redis服务器（用于异步处理）
- 支持向量数据库（ChromaDB）

### 安装步骤

```bash
# 克隆项目
git clone <repository-url>
cd mem-roleplay

# 创建虚拟环境（推荐）
python -m venv .venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install -r requirements_web.txt
```

### 环境配置

创建 `.env` 文件或设置环境变量：

```bash
# .env 文件示例
OPENAI_API_KEY="your-api-key"
OPENAI_BASE_URL="https://api.siliconflow.cn/v1"
LOG_LEVEL="INFO"

# Redis配置（用于异步处理）
REDIS_URL="redis://localhost:6379/0"
```

## 📖 基础使用

### 启动Web服务

```bash
# 启动Web服务（支持异步处理）
python run_web_service.py

# 服务启动后，访问 http://localhost:8000 查看API文档
```

### 通过HTTP API添加角色扮演对话

```python
import requests

# Web服务地址
BASE_URL = "http://localhost:8000"

# 异步添加对话记忆
payload = {
    "conversation": [
        {"role": "user", "content": "我是来自未来的时间旅行者，专门研究古代文明"},
        {"role": "assistant", "content": "听起来很酷！你最喜欢研究哪个时期的文明？"},
        {"role": "user", "content": "我对古埃及特别着迷，尤其是金字塔的建造技术"}
    ],
    "user_id": "time_traveler_001",
    "user_name": "时间旅行者"
}

response = requests.post(f"{BASE_URL}/api/v1/conversation/add", json=payload)
result = response.json()

print(f"✅ 添加结果: {result}")
if result.get('task_id'):
    print(f"异步任务ID: {result['task_id']}")
    print(f"队列长度: {result.get('queue_length', 0)}")
```

### 搜索记忆

```python
# 搜索特定用户的记忆
search_payload = {
    "user_id": "time_traveler_001",
    "query": "古埃及"
}

response = requests.post(f"{BASE_URL}/api/v1/memory/search", json=search_payload)
search_result = response.json()

print(f"🔍 搜索结果: {len(search_result.get('results', []))} 条相关记忆")
```

### 查看记忆统计

```python
# 获取用户记忆统计
stats_response = requests.get(f"{BASE_URL}/api/v1/memory/stats/time_traveler_001")
stats = stats_response.json()

print(f"📊 记忆统计:")
print(f"总记忆数: {stats.get('total_memories', 0)}")
print(f"分类统计: {stats.get('category_stats', {})}")
```

## 🔧 高级功能

### 异步处理模式

系统默认启用异步处理，对话记忆添加请求会立即返回，后台自动处理分类和存储。

```python
import requests

# 异步添加对话（默认模式）
payload = {
    "conversation": [
        {"role": "user", "content": "我喜欢科幻题材的角色扮演"},
        {"role": "assistant", "content": "科幻确实很有趣！"}
    ],
    "user_id": "async_user",
    "user_name": "异步用户"
}

response = requests.post("http://localhost:8000/api/v1/conversation/add", json=payload)
result = response.json()

if result["status"] == "success":
    if result.get("task_id"):
        print(f"✅ 异步任务已提交，任务ID: {result['task_id']}")
        print(f"当前队列长度: {result.get('queue_length', 0)}")
    else:
        print("✅ 任务已通过线程池异步处理")
```

### 队列状态监控

```python
# 查看异步队列状态
response = requests.get("http://localhost:8000/api/v1/queue/status")
queue_status = response.json()

print(f"📊 队列状态:")
print(f"活跃任务数: {queue_status.get('active_tasks', 0)}")
print(f"待处理任务数: {queue_status.get('pending_tasks', 0)}")
```

### 记忆分类查询

```python
# 按分类查询记忆
categories = ["profile", "behavioral_patterns", "roleplay_scenarios", "event", "interaction"]

for category in categories:
    payload = {
        "user_id": "test_user",
        "query": "角色",
        "category": category
    }
    
    response = requests.post("http://localhost:8000/api/v1/memory/search", json=payload)
    result = response.json()
    
    print(f"{category} 分类: {len(result.get('results', []))} 条记忆")
```

## 🏗️ 项目架构

```
mem-roleplay/
├── src/                           # 源代码目录
│   ├── config.py                 # 配置管理
│   ├── app.py                    # 主应用类
│   ├── roleplay_smart_memory_manager.py  # 角色扮演记忆管理器（核心分类逻辑）
│   ├── smart_memory_manager.py   # 基础记忆管理器
│   ├── redis_memory_queue.py     # Redis异步队列处理器
│   ├── web_service.py            # FastAPI Web服务接口
│   └── utils.py                  # 工具函数
├── templates/                     # HTML模板目录
│   └── memory_query.html         # 记忆查询页面
├── test/                         # 测试目录
│   ├── test_http_client.py       # HTTP客户端测试
│   └── test_async_functionality.py  # 异步功能测试
├── requirements.txt              # 核心依赖
├── requirements_web.txt          # Web服务依赖
├── run_web_service.py            # Web服务启动脚本
└── README.md                    # 项目文档
```

## 📊 记忆分类系统

### 7种专用分类

| 分类 | 中文名称 | 描述 | 重要性 |
|------|----------|------|--------|
| `profile` | 用户档案 | 身份设定、背景故事、特征能力 | High |
| `behavioral_patterns` | 互动模式 | 说话风格、回应模式、情感态度 | Medium |
| `internal_monologue` | 内心独白 | 真实想法、情绪变化、隐藏动机 | 动态 |
| `interaction_context` | 交互上下文 | 场景环境、关系状态、共同经历 | Medium |
| `roleplay_scenarios` | 角色扮演场景 | 题材偏好、场景设定、情节类型 | High |
| `event` | 事件记录 | 具体经历、行动记录、时间节点 | 动态 |
| `interaction` | 互动交流 | 一般对话、提问回应、临时片段 | Low |

## 🔌 API接口文档

### 添加对话记忆（异步处理）

**POST** `/api/v1/conversation/add`

添加角色扮演对话记忆，系统会自动进行智能分类和存储。

**请求体:**
```json
{
    "conversation": [
        {"role": "user", "content": "对话内容"},
        {"role": "assistant", "content": "回复内容"}
    ],
    "user_id": "用户ID",
    "user_name": "用户名"
}
```

**响应示例:**
```json
{
    "status": "success",
    "task_id": "async_task_123",
    "queue_length": 5,
    "processing_mode": "redis_queue"
}
```

### 搜索记忆

**POST** `/api/v1/memory/search`

根据查询条件搜索用户的记忆。

**请求体:**
```json
{
    "user_id": "用户ID",
    "query": "搜索关键词",
    "category": "可选分类"
}
```

### 获取记忆统计

**GET** `/api/v1/memory/stats/{user_id}`

获取指定用户的记忆统计信息。

### 异步队列管理

**GET** `/api/v1/queue/status`

获取异步队列的状态信息。

## ⚙️ 配置说明

### 环境变量

```bash
# DeepSeek配置（通过SiliconFlow）
OPENAI_API_KEY="your-siliconflow-api-key"
OPENAI_BASE_URL="https://api.siliconflow.cn/v1"

# 应用配置
LOG_LEVEL="INFO"

# Redis配置
REDIS_URL="redis://localhost:6379/0"
```

### 异步处理流程

1. **请求接收**: Web服务接收对话记忆添加请求
2. **任务分发**: 根据Redis队列可用性决定处理方式
3. **异步处理**: 后台进行LLM分类和记忆存储
4. **立即响应**: 接口立即返回任务状态，不阻塞用户

## 🐛 故障排除

### 常见问题

#### 1. Redis连接失败
**症状**: 异步处理失败，返回线程池处理
**解决方案**: 检查Redis服务器是否正常运行

#### 2. LLM服务连接失败
**症状**: 记忆分类失败
**解决方案**: 检查API密钥和网络连接

#### 3. 记忆搜索无结果
**症状**: 搜索返回空结果
**解决方案**: 确认记忆已成功添加并索引

## 📄 许可证

本项目基于 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

⭐ 如果这个项目对你有帮助，请给我们一个星标！

---

**项目特色**: 专为角色扮演优化的智能记忆系统，支持7种记忆分类和异步处理。