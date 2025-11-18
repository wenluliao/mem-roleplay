# 🎭 Mem0AI 角色扮演智能记忆系统

基于Mem0库构建的专门针对角色扮演场景优化的智能记忆管理系统，提供对话记忆管理、角色档案构建、行为模式分析等高级功能。

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Mem0](https://img.shields.io/badge/built%20with-Mem0-orange.svg)](https://github.com/mem0ai/mem0)
[![DeepSeek](https://img.shields.io/badge/LLM-DeepSeek_V3.2-brightgreen.svg)](https://www.deepseek.com/)

## ✨ 核心特性

### 🎯 角色扮演专用优化
- **智能记忆分类**: 自动识别和分类角色扮演相关记忆
- **角色档案构建**: 自动构建用户角色档案和行为模式
- **场景上下文管理**: 维护角色扮演的完整上下文信息
- **内心活动记录**: 捕捉用户的真实想法和情感变化

### 🔧 技术特性
- **多LLM支持**: 支持DeepSeek V3.2、Ollama等多种LLM后端
- **智能向量检索**: 基于语义的智能记忆搜索和匹配
- **性能监控**: 内置性能监控和优化工具
- **模块化架构**: 清晰的代码结构，易于扩展和维护

### 📊 记忆管理
- **7种记忆分类**: profile、behavioral_patterns、internal_monologue等
- **重要性分级**: 高、中、低三级重要性标记
- **生命周期管理**: 支持记忆更新、删除、清理、合并
- **访问统计**: 详细的记忆访问和使用统计

## 🚀 快速开始

### 系统要求

- Python 3.8+
- 至少2GB可用内存
- 支持向量数据库（ChromaDB）

### 安装步骤

```bash
# 克隆项目
git clone <repository-url>
cd mem0ai

# 创建虚拟环境（推荐）
python -m venv .venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 环境配置

创建 `.env` 文件或设置环境变量：

```bash
# .env 文件示例
OPENAI_API_KEY="your-api-key"
OLLAMA_BASE_URL="http://localhost:11434"
DEBUG=false
```

## 📖 基础使用

### 初始化应用

```python
from src.app import Mem0App

# 初始化角色扮演专用应用
app = Mem0App()
print("🎭 角色扮演记忆系统初始化完成")
```

### 添加角色扮演对话

```python
# 示例角色扮演对话
roleplay_messages = [
    {"role": "user", "content": "我是来自未来的时间旅行者，专门研究古代文明"},
    {"role": "assistant", "content": "听起来很酷！你最喜欢研究哪个时期的文明？"},
    {"role": "user", "content": "我对古埃及特别着迷，尤其是金字塔的建造技术"},
    {"role": "assistant", "content": "金字塔确实很神秘。你有什么特别的发现吗？"},
    {"role": "user", "content": "我发现古埃及人可能使用了某种失传的能量技术"}
]

# 添加对话并启用角色扮演分类
result = app.add_conversation(
    roleplay_messages, 
    user_id="time_traveler_001",
    enable_roleplay_classification=True
)
print(f"✅ 添加结果: {result['added_count']} 条记忆")
```

### 智能搜索记忆

```python
# 搜索角色档案信息
profile_results = app.search_by_category("profile", "time_traveler_001")
app.print_search_results(profile_results, "角色档案")

# 搜索行为模式
behavior_results = app.search_by_category("behavioral_patterns", "time_traveler_001")
app.print_search_results(behavior_results, "行为模式")
```

### 查看角色档案

```python
# 获取完整的角色档案
profile = app.get_roleplay_profile("time_traveler_001")
print(f"🎭 角色档案摘要:")
print(f"身份特征: {profile['total_traits']} 项")
print(f"行为模式: {profile['pattern_count']} 种")
print(f"场景偏好: {profile['scenario_count']} 类")

# 打印详细档案
app.print_character_profile("time_traveler_001")
```

## 🔧 高级功能

### 自定义配置

```python
# 自定义LLM配置
custom_config = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": "deepseek-ai/DeepSeek-V3.2-Exp",
            "openai_base_url": "https://api.siliconflow.cn/v1",
            "temperature": 0.2
        }
    },
    "embedder": {
        "provider": "ollama", 
        "config": {
            "model": "qwen3-embedding:0.6b",
            "ollama_base_url": "http://localhost:11434"
        }
    }
}

app = Mem0App(config_overrides=custom_config)
```

### 批量记忆操作

```python
# 批量添加多个对话场景
scenarios = [
    [{"role": "user", "content": "我喜欢科幻题材的角色扮演"}],
    [{"role": "user", "content": "我擅长扮演神秘的外星生物"}],
    [{"role": "user", "content": "我对魔法世界设定特别感兴趣"}]
]

for i, scenario in enumerate(scenarios):
    app.add_conversation(scenario, user_id=f"roleplayer_{i:03d}")
```

### 记忆清理和优化

```python
# 清理过期记忆
cleanup_result = app.cleanup_memories("time_traveler_001")
print(f"🧹 清理完成: {cleanup_result}")

# 强制删除特定记忆
deleted_count = app.force_delete_memory("测试数据", "time_traveler_001")
print(f"💥 强制删除: {deleted_count} 条记忆")
```

## 🏗️ 项目架构

```
mem0ai/
├── src/                           # 源代码目录
│   ├── config.py                 # 配置管理（支持DeepSeek V3.2）
│   ├── app.py                    # 主应用类（角色扮演优化版）
│   ├── roleplay_smart_memory_manager.py  # 角色扮演记忆管理器
│   ├── smart_memory_manager.py   # 基础记忆管理器
│   └── utils.py                  # 工具函数和性能监控
├── test/                         # 测试目录
│   ├── test_ollama.py            # Ollama集成测试
│   └── test_performance_optimized.py  # 性能测试
├── db/                           # 向量数据库存储
├── requirements.txt              # 依赖管理
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

### 使用示例

```python
# 按分类搜索记忆
scenario_memories = app.search_by_category("roleplay_scenarios", "user123")
internal_thoughts = app.search_by_category("internal_monologue", "user123")

# 获取分类统计
stats = app.get_category_statistics("user123")
for category, info in stats['categories'].items():
    print(f"{category}: {info['count']} 条 ({info['percentage']:.1f}%)")
```

## ⚙️ 配置详解

### 默认配置结构

```python
{
    "llm": {
        "provider": "openai",
        "config": {
            "model": "deepseek-ai/DeepSeek-V3.2-Exp",
            "temperature": 0.2,
            "max_tokens": 2000,
            "openai_base_url": "https://api.siliconflow.cn/v1"
        }
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "qwen3-embedding:0.6b", 
            "ollama_base_url": "http://localhost:11434"
        }
    },
    "vector_store": {
        "provider": "chroma",
        "config": {
            "collection_name": "test",
            "path": "db"
        }
    }
}
```

### 支持的LLM后端

- **DeepSeek V3.2**: 通过SiliconFlow API访问
- **Ollama**: 本地部署的LLM服务
- **OpenAI**: 标准的OpenAI API

### 环境变量配置

```bash
# DeepSeek配置（通过SiliconFlow）
OPENAI_API_KEY="your-siliconflow-api-key"
OPENAI_BASE_URL="https://api.siliconflow.cn/v1"

# Ollama配置
OLLAMA_BASE_URL="http://localhost:11434"

# 应用配置
DEBUG="true"
LOG_LEVEL="INFO"
```

## 🔍 开发指南

### 添加新的记忆分类

修改 `roleplay_smart_memory_manager.py` 中的分类系统：

```python
# 在 __init__ 方法中添加新分类
self.roleplay_categories = {
    'profile': '用户档案',
    'behavioral_patterns': '互动模式',
    # ... 现有分类
    'new_category': '新分类描述'  # 添加新分类
}

# 在提示词模板中添加新分类的描述
```

### 自定义分类逻辑

```python
def custom_classification_logic(self, messages):
    """自定义分类逻辑"""
    # 实现你的分类算法
    classified_results = []
    
    for message in messages:
        if self._is_special_pattern(message):
            classified_results.append({
                "content": message["content"],
                "category": "special_category",
                "importance": "high"
            })
    
    return classified_results
```

### 性能优化建议

1. **批量操作**: 使用批量API减少网络请求
2. **缓存策略**: 实现记忆缓存减少重复搜索
3. **异步处理**: 使用异步IO提高并发性能
4. **定期清理**: 设置记忆过期策略释放资源

## 🧪 测试和验证

### 运行基础测试

```bash
# 运行Ollama集成测试
python test/test_ollama.py

# 运行性能测试
python test/test_performance_optimized.py
```

### 验证记忆分类效果

```python
# 验证分类准确性
test_messages = [
    {"role": "user", "content": "我喜欢扮演科幻角色"},
    {"role": "user", "content": "我对古文明很感兴趣"}
]

result = app.add_conversation(test_messages, "test_user", True)
print("分类结果:", result["classified_facts"])
```

## 🐛 故障排除

### 常见问题

#### 1. LLM服务连接失败
**症状**: `ConnectionError` 或超时
**解决方案**:
- 检查API密钥有效性
- 确认网络连接正常
- 验证服务端点可访问

#### 2. 记忆分类不准确
**症状**: 分类结果不符合预期
**解决方案**:
- 调整提示词模板
- 检查对话格式是否正确
- 验证LLM响应格式

#### 3. 性能问题
**症状**: 响应缓慢或内存占用高
**解决方案**:
- 启用性能监控
- 优化批量操作大小
- 定期清理过期记忆

### 调试模式

启用详细日志输出：

```bash
# 设置调试模式
export DEBUG=true

# 运行应用
python your_script.py
```

## 🤝 贡献指南

欢迎社区贡献！请遵循以下流程：

1. Fork 项目仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 代码规范

- 遵循 PEP 8 代码风格
- 添加适当的类型注解
- 编写清晰的文档字符串
- 确保所有测试通过

## 📄 许可证

本项目基于 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Mem0](https://github.com/mem0ai/mem0) - 提供核心记忆管理功能
- [DeepSeek](https://www.deepseek.com/) - 强大的LLM模型支持
- [SiliconFlow](https://siliconflow.cn/) - 优质的AI推理服务
- [Ollama](https://ollama.ai/) - 本地LLM部署方案
- [ChromaDB](https://github.com/chroma-core/chroma) - 向量数据库支持

## 📞 支持

如有问题或建议，请通过以下方式联系：

- 提交 [Issue](https://github.com/your-repo/issues)
- 发送邮件至: your-email@example.com

---

⭐ 如果这个项目对你有帮助，请给我们一个星标！

---

**最新更新**: 项目已全面优化为角色扮演专用系统，支持DeepSeek V3.2和7种智能记忆分类。