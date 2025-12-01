import os
import logging
import json
import re
import requests
from datetime import datetime
from flask import Flask, request, jsonify, Response, stream_with_context
from dotenv import load_dotenv
from openai import OpenAI

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("chat_service.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 加载环境变量
load_dotenv()

# 初始化Flask应用
app = Flask(__name__)

# 配置OpenAI客户端
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_MODEL = os.getenv("MODEL_NAME")

# 配置MemU API
MEMU_API_KEY = os.getenv("MEMU_API_KEY", "mu_nckoEtBwEx0E-2tPl3oS2M8-iQDrdvYx2XrbYPCra6dqOjHtpn9t78-fJ7uOtyCaNBFDbG7O2JmGc-XZx-4NNrQYIUnQW2_1z_YQ_A")
# MEMU_BASE_URL = os.getenv("MEMU_BASE_URL", "https://api.memu.so/api/v1")
MEMU_BASE_URL = os.getenv("MEMU_BASE_URL", "http://127.0.0.1:8000/api/v1")

# 配置端口
PORT = int(os.getenv("PORT", 25001))

# 检查OpenAI API密钥
if not OPENAI_API_KEY:
    error_msg = "OpenAI API密钥未配置，请在.env文件中设置OPENAI_API_KEY"
    logging.error(error_msg)
    raise ValueError(error_msg)

# 初始化OpenAI客户端
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

def filter_sensitive_content(text):
    """过滤敏感内容，避免被ModelScope API拒绝"""
    if not text:
        return text
    
    # 定义敏感词列表（可以根据需要扩展）
    sensitive_patterns = [
        # 色情相关
        r'色情|情色|性爱|做爱|性交|淫秽|猥亵|淫荡|淫乱|淫靡|淫秽|淫荡|淫乱|淫靡',
        r'强奸|轮奸|奸淫|强暴|性侵|性骚扰|性虐待|性暴力',
        r'AV|A片|黄片|毛片|三级片|成人片|色情片',
        r'妓女|嫖娼|卖淫|性工作者|性交易',
        r'性器官|生殖器|阴茎|阴道|乳房|胸部|屁股|臀部',
        r'自慰|手淫|打飞机|撸管|射精|高潮|性快感',
        
        # 暴力相关
        r'杀人|谋杀|杀害|杀死|致死|死亡|尸体|死尸',
        r'暴力|殴打|打人|打架|斗殴|伤害|重伤|轻伤',
        r'恐怖|恐怖主义|恐怖分子|恐怖袭击|爆炸|炸弹',
        r'毒品|吸毒|贩毒|冰毒|海洛因|大麻|可卡因',
        r'武器|枪支|弹药|刀|匕首|凶器',
        
        # 其他敏感内容
        r'政治敏感|政府敏感|领导人敏感|国家机密',
        r'种族歧视|民族歧视|性别歧视|宗教歧视',
        r'诈骗|欺诈|骗局|传销|非法集资',
    ]
    
    filtered_text = text
    for pattern in sensitive_patterns:
        filtered_text = re.sub(pattern, '[内容已过滤]', filtered_text, flags=re.IGNORECASE)
    
    # 如果过滤后内容变化较大，返回安全提示
    if filtered_text != text and len(filtered_text.replace('[内容已过滤]', '').strip()) < len(text.strip()) * 0.3:
        return "您输入的内容包含较多敏感信息，请重新输入合适的内容。"
    
    return filtered_text

def preprocess_messages(messages):
    """预处理消息，过滤敏感内容"""
    processed_messages = []
    
    for msg in messages:
        if isinstance(msg, dict) and 'content' in msg:
            filtered_content = filter_sensitive_content(msg['content'])
            processed_msg = msg.copy()
            processed_msg['content'] = filtered_content
            processed_messages.append(processed_msg)
        else:
            processed_messages.append(msg)
    
    return processed_messages

@app.post('/v1/chat/completions')
def chat_completions():
    """聊天完成API，集成记忆管理，支持流式和非流式响应"""
    data = request.get_json()
    messages = data.get("messages", [])
    user_id = data.get("user_id","test_user_002")
    agent_id = data.get("agent_id", "test_user_001")
    stream = data.get("stream", False)

    if not messages:
        return jsonify({"error": "Missing required field: messages"}), 400

    # 1. 检索相关记忆
    memories = []
    use_memory = user_id is not None and agent_id is not None
    if use_memory:
        try:
            # 获取最后一条用户消息作为查询内容
            query_content = ""
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    query_content = msg.get("content", "")
                    break
            
            mem_response = requests.post(
                f'{MEMU_BASE_URL}/memory/search',
                json={
                    "user_id": user_id,
                    "agent_id": agent_id,
                    "query": query_content,
                    "limit": 5
                },
                headers={
                    'Authorization': f'Bearer {MEMU_API_KEY}',
                    'Content-Type': 'application/json; charset=utf-8'
                }
            )
            mem_response.raise_for_status()
            response_data = mem_response.json()

            logging.info(json.dumps(response_data, ensure_ascii=False))
            
            # 提取记忆项
            if isinstance(response_data, dict) and "results" in response_data:
                memories = response_data["results"]
            elif isinstance(response_data, list):
                memories = response_data
                
            logging.info(f"Retrieved {len(memories)} related memories")
        except Exception as e:
            logging.error(f"Error retrieving memories: {str(e)}")
            # 记忆检索失败时仍继续处理

    # 2. 组合消息（记忆 + 当前对话）
    combined_messages = []

    # 添加记忆作为上下文
    for mem in memories:
        if isinstance(mem, dict) and mem.get("memory"):
            combined_messages.append({"role": "user", "content": "记忆："+mem["memory"]})

    # 添加当前用户消息
    combined_messages.extend(messages)

    # 3. 预处理消息，过滤敏感内容
    processed_messages = preprocess_messages(combined_messages)
    
    # 记录预处理结果
    if processed_messages != combined_messages:
        logging.info(json.dumps(processed_messages, ensure_ascii=False))

    # 4. 构建OpenAI API参数
    params = data.copy()
    params["messages"] = processed_messages
    params["model"] = OPENAI_MODEL
    params.pop("stream_options", None)  # 移除不支持的stream_options参数

    # 4. 处理流式和非流式响应
    if stream:
        # 流式响应处理
        @stream_with_context
        def generate_stream():
            full_response_content = ""
            response_id = None
            response_model = None
            response_created = None
            
            try:
                # 调用OpenAI API获取流式响应（移除user_id等非OpenAI参数）
                openai_params = {k: v for k, v in params.items() if k not in ['user_id', 'agent_id', 'use_memory']}
                openai_response = client.chat.completions.create(**openai_params)
                
                # 处理流式响应
                for chunk in openai_response:
                    if chunk.choices and chunk.choices[0].delta:
                        delta = chunk.choices[0].delta
                        
                        # 收集完整的响应内容用于记忆存储
                        if delta.content:
                            full_response_content += delta.content
                        
                        # 收集响应元数据
                        if not response_id:
                            response_id = chunk.id
                        if not response_model:
                            response_model = chunk.model
                        if not response_created:
                            response_created = int(chunk.created)
                        
                        chunk_data = {
                            "id": chunk.id,
                            "object": "chat.completion.chunk",
                            "created": int(chunk.created),
                            "model": chunk.model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {
                                        "role": delta.role,
                                        "content": delta.content
                                    } if delta.content else {},
                                    "finish_reason": chunk.choices[0].finish_reason
                                }
                            ]
                        }
                        yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                
                # 发送结束标记
                yield "data: [DONE]\n\n"
                
                # 流式响应完成后，进行记忆存储
                if use_memory and full_response_content:
                    try:
                        # 构建记忆项用于存储
                        memory_items = []
                        
                        # 只添加最后一条用户消息
                        user_messages = [msg for msg in messages if msg.get("role") == "user"]
                        if user_messages:
                            last_user_msg = user_messages[-1]
                            memory_items.append({
                                "role": "user",
                                "content": last_user_msg.get("content", "")
                            })
                        
                        # 添加助手回复
                        memory_items.append({
                            "role": "assistant",
                            "content": full_response_content
                        })

                        # 根据MemU API文档构建完整的conversation格式
                        conversation = []
                        current_time = datetime.now().isoformat()
                        
                        for i, item in enumerate(memory_items):
                            conversation_item = {
                                "role": item["role"],
                                "content": item["content"]
                            }
                            
                            # 根据文档添加可选字段
                            if item["role"] == "user":
                                conversation_item["name"] = user_id
                            elif item["role"] == "assistant":
                                conversation_item["name"] = agent_id
                            
                            # 添加时间戳（文档示例格式）
                            conversation_item["time"] = current_time
                            
                            conversation.append(conversation_item)
                        
                        # 构建完整的请求体，只提供conversation字段
                        mem_request_body = {
                            "conversation": conversation,
                            "user_id": user_id,
                            "user_name": user_id,  # 使用user_id作为user_name
                            "agent_id": agent_id,
                            "agent_name": agent_id,  # 使用agent_id作为agent_name
                            "session_date": datetime.now().strftime("%Y-%m-%d")  # 添加会话日期
                        }
                        
                        logging.info(f"Stream mode - MemU memorize request body: {json.dumps(mem_request_body, ensure_ascii=False)}")
                        
                        mem_response = requests.post(
                            f'{MEMU_BASE_URL}/conversation/add',
                            json=mem_request_body,
                            headers={
                                'Authorization': f'Bearer {MEMU_API_KEY}',
                                'Content-Type': 'application/json; charset=utf-8'
                            }
                        )
                        
                        # 记录响应状态和内容
                        logging.info(f"Stream mode - MemU memorize response status: {mem_response.status_code}")
                        if mem_response.status_code != 200:
                            logging.error(f"Stream mode - MemU memorize response content: {mem_response.text}")
                        
                        mem_response.raise_for_status()
                        response_data = mem_response.json()
                        logging.info(f"Stream mode - Successfully memorized conversation, task_id: {response_data.get('task_id', 'unknown')}")
                            
                    except Exception as e:
                        logging.error(f"Stream mode - Error memorizing conversation: {str(e)}")
                        # 记忆失败时不中断流式响应
                        
            except Exception as e:
                logging.error(f"Stream error: {str(e)}")
                error_data = {"error": str(e)}
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

        return Response(generate_stream(), mimetype='text/plain; charset=utf-8')
    
    else:
        # 非流式响应处理
        try:
            # 调用OpenAI API（移除user_id等非OpenAI参数）
            openai_params = {k: v for k, v in params.items() if k not in ['user_id', 'agent_id', 'use_memory']}
            openai_response = client.chat.completions.create(**openai_params)
            
            # 记忆当前对话
            if use_memory:
                try:
                    # 构建记忆项用于存储
                    memory_items = []
                    
                    # 只添加最后一条用户消息
                    user_messages = [msg for msg in messages if msg.get("role") == "user"]
                    if user_messages:
                        last_user_msg = user_messages[-1]
                        memory_items.append({
                            "role": "user",
                            "content": last_user_msg.get("content", "")
                        })
                    
                    # 添加助手回复
                    memory_items.append({
                        "role": "assistant",
                        "content": openai_response.choices[0].message.content
                    })

                    # 根据MemU API文档构建完整的conversation格式
                    conversation = []
                    current_time = datetime.now().isoformat()
                    
                    for i, item in enumerate(memory_items):
                        conversation_item = {
                            "role": item["role"],
                            "content": item["content"]
                        }
                        
                        # 根据文档添加可选字段
                        if item["role"] == "user":
                            conversation_item["name"] = user_id
                        elif item["role"] == "assistant":
                            conversation_item["name"] = agent_id
                        
                        # 添加时间戳（文档示例格式）
                        conversation_item["time"] = current_time
                        
                        conversation.append(conversation_item)
                    
                    # 构建完整的请求体，只提供conversation字段
                    mem_request_body = {
                        "conversation": conversation,
                        "user_id": user_id,
                        "user_name": user_id,  # 使用user_id作为user_name
                        "agent_id": agent_id,
                        "agent_name": agent_id,  # 使用agent_id作为agent_name
                        "session_date": datetime.now().strftime("%Y-%m-%d")  # 添加会话日期
                    }
                    
                    logging.info(f"Non-stream mode - MemU memorize request body: {json.dumps(mem_request_body, ensure_ascii=False)}")
                    
                    mem_response = requests.post(
                        f'{MEMU_BASE_URL}/memory/memorize',
                        json=mem_request_body,
                        headers={
                            'Authorization': f'Bearer {MEMU_API_KEY}',
                            'Content-Type': 'application/json; charset=utf-8'
                        }
                    )
                    
                    # 记录响应状态和内容
                    logging.info(f"Non-stream mode - MemU memorize response status: {mem_response.status_code}")
                    if mem_response.status_code != 200:
                        logging.error(f"Non-stream mode - MemU memorize response content: {mem_response.text}")
                    
                    mem_response.raise_for_status()
                    response_data = mem_response.json()
                    logging.info(f"Non-stream mode - Successfully memorized conversation, task_id: {response_data.get('task_id', 'unknown')}")
                        
                except Exception as e:
                    logging.error(f"Non-stream mode - Error memorizing conversation: {str(e)}")
                    # 记忆失败时仍返回OpenAI响应

            # 返回非流式响应
            response_data = {
                "id": openai_response.id,
                "object": "chat.completion",
                "created": int(openai_response.created),
                "model": openai_response.model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": openai_response.choices[0].message.role,
                            "content": openai_response.choices[0].message.content
                        },
                        "finish_reason": openai_response.choices[0].finish_reason
                    }
                ],
                "usage": {
                    "prompt_tokens": openai_response.usage.prompt_tokens,
                    "completion_tokens": openai_response.usage.completion_tokens,
                    "total_tokens": openai_response.usage.total_tokens
                }
            }
            return jsonify(response_data), 200

        except Exception as e:
            logging.error(f"OpenAI API error: {str(e)}")
            return jsonify({"error": str(e)}), 500

@app.get('/health')
def health_check():
    """健康检查"""
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    logging.info(f"Chat service starting on port {PORT}...")
    logging.info(f"OpenAI Model: {OPENAI_MODEL}")
    logging.info(f"MemU Base URL: {MEMU_BASE_URL}")
    app.run(host='0.0.0.0', port=PORT, debug=True)