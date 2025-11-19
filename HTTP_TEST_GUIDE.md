# Mem0AI HTTP测试工具使用指南

## 📋 概述

本项目已将原有的`test_ollama.py`测试工具改造为支持HTTP访问的测试工具，现在您可以通过HTTP API来测试Mem0AI的所有功能。

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装Web服务依赖
pip install -r requirements_web.txt

# 或者安装所有依赖
pip install -r requirements.txt
```

### 2. 启动Redis服务

确保Redis服务正在运行：

```bash
# Windows (如果已安装Redis)
redis-server

# 或者使用Docker
docker run -d -p 6379:6379 redis:latest
```

### 3. 运行综合测试工具

```bash
python test_web_service.py
```

选择操作模式：
- **模式1**: 启动Web服务并运行完整测试
- **模式2**: 启动Web服务并运行快速测试  
- **模式3**: 连接到已运行的Web服务进行测试
- **模式4**: 仅启动Web服务

## 🔧 手动测试方法

### 方法1: 直接运行HTTP客户端测试

```bash
# 启动Web服务（新终端）
python run_web_service.py

# 运行HTTP测试（另一个终端）
python -c "from test.test_http_client import run_all_tests; run_all_tests('http://localhost:8000')"
```

### 方法2: 使用快速测试

```bash
# 快速功能验证
python -c "from test.test_http_client import quick_test; quick_test('http://localhost:8000')"
```

### 方法3: 运行特定测试

```bash
# 只测试角色扮演功能
python -c "from test.test_http_client import run_specific_test; run_specific_test('roleplay', 'http://localhost:8000')"

# 只测试基本功能
python -c "from test.test_http_client import run_specific_test; run_specific_test('basic', 'http://localhost:8000')"
```

## 🌐 HTTP API端点

### 健康检查
```http
GET http://localhost:8000/
```

### 添加对话记忆
```http
POST http://localhost:8000/conversation
Content-Type: application/json

{
    "user_input": "你好，我想了解人工智能",
    "assistant_response": "人工智能是模拟人类智能的计算机系统",
    "metadata": {
        "user_id": "test_user_123",
        "session_id": "session_456"
    }
}
```

### 搜索记忆
```http
POST http://localhost:8000/search
Content-Type: application/json

{
    "query": "人工智能",
    "user_id": "test_user_123",
    "limit": 10
}
```

### 队列状态
```http
GET http://localhost:8000/queue/status
```

### 清空队列
```http
POST http://localhost:8000/queue/clear
```

## 📊 测试覆盖的功能

### ✅ 基本功能测试
- 服务健康检查
- 对话记忆添加
- 记忆搜索和检索
- 记忆更新和删除

### ✅ 角色扮演功能测试  
- 角色分类和记忆组织
- 多角色对话管理
- 角色特定的记忆检索

### ✅ 高级功能测试
- 异步队列处理
- 批量操作
- 性能测试
- 错误处理

### ✅ 边界情况测试
- 空输入处理
- 超长文本处理
- 并发访问测试

## 🔍 监控和调试

### 查看队列状态
```bash
curl http://localhost:8000/queue/status
```

### 查看服务日志
Web服务启动时会显示详细的处理日志，包括：
- 请求处理状态
- 队列处理进度
- 错误信息

### 性能监控
测试工具会自动测量：
- 响应时间
- 吞吐量
- 内存使用情况

## 🛠️ 故障排除

### 常见问题

1. **连接被拒绝**
   - 检查Web服务是否启动
   - 确认端口8000未被占用

2. **Redis连接错误**
   - 确保Redis服务正在运行
   - 检查Redis配置

3. **导入错误**
   - 确保所有依赖已安装
   - 检查Python路径设置

### 调试模式

启动Web服务时添加调试标志：
```bash
python run_web_service.py --debug
```

## 📈 性能优化建议

1. **调整队列参数**
   - 修改批量处理大小
   - 调整处理线程数量

2. **优化Redis配置**
   - 增加内存限制
   - 启用持久化

3. **网络优化**
   - 使用本地网络
   - 减少请求大小

## 🎯 下一步

- [ ] 添加Web界面用于可视化测试
- [ ] 实现自动化测试流水线
- [ ] 添加性能基准测试
- [ ] 支持多环境测试配置

---

**享受使用Mem0AI HTTP测试工具！** 🚀