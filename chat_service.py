import os
import logging
import json
import re
import requests
from datetime import datetime
from flask import Flask, request, jsonify, Response, stream_with_context
from dotenv import load_dotenv
from openai import OpenAI
from google import genai
from google.genai import types


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

# 配置AI客户端
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")  # openai 或 google

# 配置OpenAI客户端
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_MODEL = os.getenv("MODEL_NAME")

# 配置Google GenAI客户端
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash")

# 配置MemU API
MEMU_API_KEY = os.getenv("MEMU_API_KEY", "mu_nckoEtBwEx0E-2tPl3oS2M8-iQDrdvYx2XrbYPCra6dqOjHtpn9t78-fJ7uOtyCaNBFDbG7O2JmGc-XZx-4NNrQYIUnQW2_1z_YQ_A")
MEMU_BASE_URL = os.getenv("MEMU_BASE_URL", "http://127.0.0.1:8000/api/v1")

# 配置端口
PORT = int(os.getenv("PORT", 25001))

# 初始化AI客户端
client = None

if AI_PROVIDER == "openai":
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
elif AI_PROVIDER == "google" and genai is not None:
    # 检查Google API密钥
    if not GOOGLE_API_KEY:
        error_msg = "Google API密钥未配置，请在.env文件中设置GOOGLE_API_KEY"
        logging.error(error_msg)
        raise ValueError(error_msg)
    
    # 初始化Google GenAI客户端
    client = genai.Client(
        api_key=GOOGLE_API_KEY,
    )
else:
    error_msg = f"不支持的AI提供商: {AI_PROVIDER} 或未安装google-generativeai包"
    logging.error(error_msg)
    raise ValueError(error_msg)

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
    user_id = data.get("user_id", "test_user_002")
    agent_id = data.get("agent_id", "test_user_001")
    stream = data.get("stream", False)
    
    # 提取模型参数（如果提供）
    model = data.get("model")
    
    # 设置响应头为SSE
    headers = {
        'Content-Type': 'text/event-stream; charset=utf-8',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no'  # 禁用Nginx缓冲
    }

    if not messages:
        if stream:
            def generate_error():
                error_data = {"error": "Missing required field: messages"}
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            return Response(generate_error(), headers=headers, mimetype='text/event-stream')
        else:
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

            logging.info(f"Retrieved memories: {json.dumps(response_data, ensure_ascii=False)}")
            
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
            combined_messages.append({"role": "user", "content": "记忆：" + mem["memory"]})

    # 添加当前用户消息
    combined_messages.extend(messages)

    # 3. 预处理消息，过滤敏感内容
    processed_messages = preprocess_messages(combined_messages)
    
    # 记录预处理结果
    if processed_messages != combined_messages:
        logging.info(f"Processed messages: {json.dumps(processed_messages, ensure_ascii=False)}")

    if stream:
        # 流式响应处理
        @stream_with_context
        def generate_stream():
            full_response_content = ""
            
            try:
                if AI_PROVIDER == "openai":
                    # OpenAI API调用
                    params = {
                        "messages": processed_messages,
                        "model": model or OPENAI_MODEL,
                        "stream": True
                    }
                    
                    # 调用OpenAI API
                    response_stream = client.chat.completions.create(**params)
                    
                    # 处理OpenAI流式响应
                    for chunk in response_stream:
                        if chunk.choices and chunk.choices[0].delta:
                            delta = chunk.choices[0].delta
                            
                            # 收集完整的响应内容用于记忆存储
                            if delta and delta.content:
                                full_response_content += delta.content
                            
                            chunk_data = {
                                "id": chunk.id,
                                "object": "chat.completion.chunk",
                                "created": int(chunk.created),
                                "model": chunk.model,
                                "choices": [
                                    {
                                        "index": 0,
                                        "delta": {
                                            "role": delta.role if delta.role else "assistant",
                                            "content": delta.content if delta.content else ""
                                        },
                                        "finish_reason": chunk.choices[0].finish_reason
                                    }
                                ]
                            }
                            yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                    
                    # 发送结束标记
                    yield "data: [DONE]\n\n"
                    
                elif AI_PROVIDER == "google" and genai is not None:
                    # Google GenAI API调用
                    import uuid
                    response_id = f"chatcmpl-{str(uuid.uuid4())}"
                    response_created = int(datetime.now().timestamp())
                    response_model = model or GOOGLE_MODEL
                    
                    # 转换消息格式为Google GenAI格式
                    contents = []
                    system_instruction = ""
                    
                    for msg in processed_messages:
                        if msg["role"] == "system":
                            system_instruction = msg["content"]
                        else:
                            contents.append(
                                types.Content(
                                    role="user" if msg["role"] == "user" else "model",
                                    parts=[types.Part.from_text(text=msg["content"])],
                                )
                            )
                    
                    # 配置生成参数
                    generate_content_config = types.GenerateContentConfig(
                        thinkingConfig={'thinkingBudget': 0},
                        safety_settings=[
                            types.SafetySetting(
                                category="HARM_CATEGORY_HARASSMENT",
                                threshold="BLOCK_NONE",
                            ),
                            types.SafetySetting(
                                category="HARM_CATEGORY_HATE_SPEECH",
                                threshold="BLOCK_NONE",
                            ),
                            types.SafetySetting(
                                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                                threshold="BLOCK_NONE",
                            ),
                            types.SafetySetting(
                                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                                threshold="BLOCK_NONE",
                            ),
                        ],
                        system_instruction=[types.Part.from_text(text=system_instruction)] if system_instruction else None
                    )
                    
                    # 调用Google GenAI API
                    response_stream = client.models.generate_content_stream(
                        model=response_model,
                        contents=contents,
                        config=generate_content_config,
                    )
                    
                    # 处理Google GenAI流式响应
                    has_sent_initial_chunk = False
                    
                    for chunk in response_stream:
                        if hasattr(chunk, 'text') and chunk.text:
                            chunk_text = chunk.text
                            full_response_content += chunk_text
                            
                            # 构建delta
                            delta = {"content": chunk_text}
                            
                            # 第一次发送时包含role
                            if not has_sent_initial_chunk:
                                delta["role"] = "assistant"
                                has_sent_initial_chunk = True
                            
                            chunk_data = {
                                "id": response_id,
                                "object": "chat.completion.chunk",
                                "created": response_created,
                                "model": response_model,
                                "choices": [
                                    {
                                        "index": 0,
                                        "delta": delta,
                                        "finish_reason": None
                                    }
                                ]
                            }
                            
                            # 使用SSE格式
                            yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                    
                    # 发送结束chunk
                    final_data = {
                        "id": response_id,
                        "object": "chat.completion.chunk",
                        "created": response_created,
                        "model": response_model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {},
                                "finish_reason": "stop"
                            }
                        ]
                    }
                    yield f"data: {json.dumps(final_data, ensure_ascii=False)}\n\n"
                    
                    # 发送结束标记
                    yield "data: [DONE]\n\n"
                
                else:
                    # 不支持的AI提供商
                    error_data = {"error": f"Unsupported AI provider: {AI_PROVIDER}"}
                    yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                    yield "data: [DONE]\n\n"
                
            except Exception as e:
                logging.error(f"Stream error: {str(e)}")
                error_data = {"error": str(e)}
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
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

                    # 构建完整的请求体
                    mem_request_body = {
                        "conversation": memory_items,
                        "user_id": user_id,
                        "agent_id": agent_id
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
                    
                    logging.info(f"Stream mode - MemU memorize response status: {mem_response.status_code}")
                    if mem_response.status_code == 200:
                        response_data = mem_response.json()
                        logging.info(f"Stream mode - Successfully memorized conversation, task_id: {response_data.get('task_id', 'unknown')}")
                    else:
                        logging.error(f"Stream mode - MemU memorize error: {mem_response.text}")
                        
                except Exception as e:
                    logging.error(f"Stream mode - Error memorizing conversation: {str(e)}")

        return Response(generate_stream(), headers=headers, mimetype='text/event-stream')
    
    else:
        # 非流式响应处理
        try:
            if AI_PROVIDER == "openai":
                # OpenAI API调用
                params = {
                    "messages": processed_messages,
                    "model": model or OPENAI_MODEL,
                    "stream": False
                }
                
                response = client.chat.completions.create(**params)
                
                # 格式化响应
                formatted_response = {
                    "id": response.id,
                    "object": "chat.completion",
                    "created": int(response.created),
                    "model": response.model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": response.choices[0].message.role,
                                "content": response.choices[0].message.content
                            },
                            "finish_reason": response.choices[0].finish_reason
                        }
                    ],
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                        "total_tokens": response.usage.total_tokens if response.usage else 0
                    }
                }
                
            elif AI_PROVIDER == "google" and genai is not None:
                # Google GenAI API调用
                import uuid
                response_id = f"chatcmpl-{str(uuid.uuid4())}"
                response_created = int(datetime.now().timestamp())
                response_model = model or GOOGLE_MODEL
                
                # 转换消息格式为Google GenAI格式
                contents = []
                system_instruction = ""
                
                for msg in processed_messages:
                    if msg["role"] == "system":
                        system_instruction = msg["content"]
                    else:
                        contents.append(
                            types.Content(
                                role="user" if msg["role"] == "user" else "model",
                                parts=[types.Part.from_text(text=msg["content"])],
                            )
                        )
                
                # 配置生成参数
                generate_content_config = types.GenerateContentConfig(
                    thinkingConfig={'thinkingBudget': 0},
                    safety_settings=[
                        types.SafetySetting(
                            category="HARM_CATEGORY_HARASSMENT",
                            threshold="BLOCK_NONE",
                        ),
                        types.SafetySetting(
                            category="HARM_CATEGORY_HATE_SPEECH",
                            threshold="BLOCK_NONE",
                        ),
                        types.SafetySetting(
                            category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                            threshold="BLOCK_NONE",
                        ),
                        types.SafetySetting(
                            category="HARM_CATEGORY_DANGEROUS_CONTENT",
                            threshold="BLOCK_NONE",
                        ),
                    ],
                    system_instruction=[types.Part.from_text(text=system_instruction)] if system_instruction else None
                )
                
                # 调用Google GenAI API
                response = client.models.generate_content(
                    model=response_model,
                    contents=contents,
                    config=generate_content_config,
                )
                
                # 提取响应文本
                response_text = ""
                if hasattr(response, 'text'):
                    response_text = response.text
                elif hasattr(response, 'candidates') and response.candidates:
                    response_text = response.candidates[0].content.parts[0].text if response.candidates[0].content.parts else ""
                
                # 格式化响应
                formatted_response = {
                    "id": response_id,
                    "object": "chat.completion",
                    "created": response_created,
                    "model": response_model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": response_text
                            },
                            "finish_reason": "stop"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0
                    }
                }
                
            else:
                return jsonify({"error": f"Unsupported AI provider: {AI_PROVIDER}"}), 400
            
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
                        "content": formatted_response["choices"][0]["message"]["content"]
                    })

                    # 构建完整的请求体
                    mem_request_body = {
                        "conversation": memory_items,
                        "user_id": user_id,
                        "agent_id": agent_id
                    }
                    
                    logging.info(f"Non-stream mode - MemU memorize request body: {json.dumps(mem_request_body, ensure_ascii=False)}")
                    
                    mem_response = requests.post(
                        f'{MEMU_BASE_URL}/conversation/add',
                        json=mem_request_body,
                        headers={
                            'Authorization': f'Bearer {MEMU_API_KEY}',
                            'Content-Type': 'application/json; charset=utf-8'
                        }
                    )
                    
                    logging.info(f"Non-stream mode - MemU memorize response status: {mem_response.status_code}")
                    if mem_response.status_code == 200:
                        response_data = mem_response.json()
                        logging.info(f"Non-stream mode - Successfully memorized conversation, task_id: {response_data.get('task_id', 'unknown')}")
                    else:
                        logging.error(f"Non-stream mode - MemU memorize error: {mem_response.text}")
                        
                except Exception as e:
                    logging.error(f"Non-stream mode - Error memorizing conversation: {str(e)}")
            
            return jsonify(formatted_response), 200
            
        except Exception as e:
            logging.error(f"AI API error: {str(e)}")
            return jsonify({"error": str(e)}), 500

@app.get('/health')
def health_check():
    """健康检查"""
    return jsonify({"status": "ok"}), 200

@app.get('/')
def index():
    """首页"""
    return jsonify({
        "service": "Chat API Service",
        "ai_provider": AI_PROVIDER,
        "models": {
            "openai": OPENAI_MODEL if AI_PROVIDER == "openai" else None,
            "google": GOOGLE_MODEL if AI_PROVIDER == "google" else None
        },
        "endpoints": {
            "chat": "/v1/chat/completions (POST)",
            "health": "/health (GET)"
        }
    }), 200

if __name__ == "__main__":
    logging.info(f"Chat service starting on port {PORT}...")
    logging.info(f"AI Provider: {AI_PROVIDER}")
    if AI_PROVIDER == "openai":
        logging.info(f"OpenAI Model: {OPENAI_MODEL}")
    elif AI_PROVIDER == "google":
        logging.info(f"Google Model: {GOOGLE_MODEL}")
    logging.info(f"MemU Base URL: {MEMU_BASE_URL}")
    app.run(host='0.0.0.0', port=PORT, debug=True)