from .smart_memory_manager import SmartMemoryManager
from .config import config
import time
import json

class RoleplaySmartMemoryManager(SmartMemoryManager):
    """角色扮演专用的智能记忆管理器 - 完整版"""
    
    def __init__(self, memory_client=None, use_async=False):
        super().__init__(memory_client)
        self.roleplay_categories = {
            'profile': '用户档案',
            'behavioral_patterns': '互动模式', 
            'internal_monologue': '内心独白',
            'interaction_context': '交互上下文',
            'roleplay_scenarios': '角色扮演场景',
            'event': '事件',
            'interaction': '互动交流'
        }
        self.use_async = use_async
        if use_async:
            # 使用Redis队列（暂时禁用，因为RedisMemoryQueue类未实现）
            print("⚠️  异步处理功能暂时不可用，使用同步处理模式")
            # self.async_processor = RedisMemoryQueue(self)
            # import threading
            # self.process_thread = threading.Thread(target=self.async_processor.start_processing, daemon=True)
            # self.process_thread.start()
    
    def add_conversation_with_roleplay_classification(self, messages, user_id):
        """
        使用角色扮演分类添加对话
        """
        user_messages = messages
        # user_messages = [msg for msg in messages if msg["role"] == "user"]
        
        print("🎭 开始角色扮演记忆分类...")
        start_time = time.time()
        
        # 提取角色扮演事实
        classified_facts = self._extract_roleplay_facts(user_messages)
        
        classification_time = time.time() - start_time
        print(f"🎭 分类完成，耗时: {classification_time:.2f}s")
        print(json.dumps(classified_facts, ensure_ascii=False, indent=3))
        
        # 显示分类结果
        print("🎭 角色扮演记忆分类结果:")
        for fact in classified_facts["facts"]:
            print(f"  📁 {fact['category']} | ⚡ {fact['importance']} | {fact['content']}")
            if 'reasoning' in fact:
                print(f"     💡 {fact['reasoning']}")

        # 批量添加记忆
        if self.use_async and hasattr(self, 'async_processor'):
            # 异步处理
            self.async_processor.add_memories(classified_facts["facts"], user_id)
            return {
                "classified_facts": classified_facts,
                "processing_mode": "async",
                "queue_stats": self.async_processor.get_queue_stats(),
                "classification_time": classification_time
            }
        else:
            # 同步处理
            result = self.add_roleplay_memories_batch(classified_facts["facts"], user_id)
            total_time = time.time() - start_time
            return {
                "classified_facts": classified_facts,
                "processing_mode": "sync",
                "added_count": result["added_count"],
                "total_time": total_time
            }
        

    def _extract_roleplay_facts(self, user_messages):
        """提取角色扮演专用事实 - 保留完整对话上下文"""
        # 保留完整的对话结构，但正确格式化
        try:
            # 构建完整的对话上下文，包括user和assistant的发言
            formatted_dialogue = self._format_dialogue_for_llm(user_messages)
            return self._llm_based_classification(formatted_dialogue)
        except Exception as e:
            print(f"LLM分类失败: {e}")
            return {"facts": []}

    def _format_dialogue_for_llm(self, messages):
        """将对话格式化为LLM友好的格式"""
        dialogue_lines = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role == "user":
                dialogue_lines.append(f"用户: {content}")
            elif role == "assistant":
                dialogue_lines.append(f"助手: {content}")
            else:
                dialogue_lines.append(f"{role}: {content}")
        
        return "\n".join(dialogue_lines)

    def _llm_based_classification(self, formatted_dialogue):
        """基于LLM的精细分类 - 使用完整对话"""
        prompt_content = self._create_enhanced_roleplay_prompt().format(
            user_messages=formatted_dialogue
        )
        
        # 调试输出，确认内容正确
        print("🔍 发送给LLM的对话内容:")
        print(formatted_dialogue)
        print("=" * 50)
        
        # 调用LLM进行分类
        response = self._call_llm_for_roleplay_classification(prompt_content)
        return response

    def _create_enhanced_roleplay_prompt(self):
        """优化版角色扮演提示词 - 保持原始角色称谓"""
        return """# 角色：角色扮演记忆分析师
        ## 核心任务：
        从角色扮演对话中提取user（用户）的重要发言，进行智能分类和重要性评估。

        ## 重要说明：
        - 记录user用户称为用户，assistant用户称为助手。

        ## 分类指南：

        ### 📋 profile (用户档案) - 身份核心信息
        - 用户的身份设定、背景故事
        - 用户的特征、能力、限制
        - 用户的基本信息、偏好、禁忌
        - *重要性：high*

        ### 🔄 behavioral_patterns (互动模式) - 行为习惯  
        - 用户的说话风格和回应模式
        - 用户的互动偏好和情感态度
        - 用户的行为习惯和反应方式
        - 用户和助手为自己定义的名字，别称等
        - *重要性：medium*

        ### 💭 internal_monologue (内心活动) - 真实想法
        - 用户表达的真实想法和感受
        - 用户的情绪变化和内心矛盾
        - 用户未明确表达的隐藏动机
        - *重要性：根据情感强度*

        ### 🌍 interaction_context (互动背景) - 场景关系
        - 用户描述的当前场景和环境
        - 用户表达的关系状态和信任程度
        - 用户提到的共同经历和回忆
        - *重要性：medium*

        ### 🎭 roleplay_scenarios (扮演场景) - 剧情偏好
        - 用户喜欢的题材和剧情类型
        - 用户偏好的场景设定和情节
        - 用户想体验的角色和情境
        - *重要性：high*

        ### ⏰ event (事件记录) - 具体经历
        - 用户描述的经历或计划
        - 用户的行动记录和打算
        - 用户提到的重要时间节点
        - *重要性：根据事件重要性*

        ### 💬 interaction (互动交流) - 对话内容
        - 用户的一般性对话和交流
        - 用户的提问和简单回应
        - 临时的对话片段
        - *重要性：low*


        用户和助手的对话记录：
        {user_messages}

        请按以下JSON格式返回分类结果：
        {{
        "facts": [
            {{
            "content": "以第三人称视角来描述用户的事件行为或者心理，不要去揣测意图。",
            "category": "分类类型", 
            "importance": "重要性级别",
            "reasoning": "分类理由"
            }}
        ]
        }}"""

    def _call_llm_for_roleplay_classification(self, prompt_content):
        """调用LLM进行角色扮演分类 - 真实实现"""
        try:
            print("🤖 正在调用LLM进行角色扮演分类...")
            
            # 导入必要的模块
            from openai import OpenAI
            import json
            
            # 创建OpenAI客户端
            client = OpenAI(
                base_url=config.get_llm_config()["config"]["openai_base_url"],
                api_key=config.get_llm_config()["config"]["api_key"]
            )
            
            # 调用LLM
            response = client.chat.completions.create(
                model=config.get_llm_config()["config"]["model"],
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的角色扮演记忆分类专家，请严格按照要求的JSON格式返回结果。"
                    },
                    {
                        "role": "user", 
                        "content": prompt_content
                    }
                ],
                temperature=0.1,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            # 解析响应
            response_content = response.choices[0].message.content
            print(f"📄 LLM原始响应: {response_content}")
            
            # 解析JSON
            try:
                result = json.loads(response_content)
                
                # 验证结果格式
                if "facts" in result and isinstance(result["facts"], list):
                    print(f"✅ LLM分类成功，提取到 {len(result['facts'])} 条事实")
                    return result
                else:
                    print("❌ LLM返回格式不正确")
                    return {"facts": []}
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {e}")
                return {"facts": []}
                
        except Exception as e:
            print(f"❌ LLM调用失败: {e}")
            return {"facts": []}

    def get_memories_by_roleplay_category(self, user_id, category):
        """按角色扮演分类获取记忆"""
        all_memories = self.get_all_memories(user_id)
        
        category_memories = []
        for memory in all_memories["results"]:
            metadata = memory.get("metadata", {})
            if metadata.get("category") == category and metadata.get("roleplay_context"):
                category_memories.append(memory)
        
        return {
            "category": category,
            "count": len(category_memories),
            "memories": category_memories
        }
    
    def print_roleplay_memory_stats(self, user_id):
        """打印角色扮演记忆统计"""
        stats = {}
        for category in self.roleplay_categories.keys():
            result = self.get_memories_by_roleplay_category(user_id, category)
            stats[category] = result["count"]
        
        print("🎭 角色扮演记忆分类统计:")
        for category, count in stats.items():
            chinese_name = self.roleplay_categories[category]
            print(f"  {chinese_name}({category}): {count} 条")
    
    def get_roleplay_profile(self, user_id):
        """获取角色扮演档案摘要"""
        profile_memories = self.get_memories_by_roleplay_category(user_id, "profile")
        behavioral_memories = self.get_memories_by_roleplay_category(user_id, "behavioral_patterns")
        scenario_memories = self.get_memories_by_roleplay_category(user_id, "roleplay_scenarios")
        
        return {
            "user_id": user_id,
            "profile_traits": len(profile_memories["memories"]),
            "behavioral_patterns": len(behavioral_memories["memories"]),
            "preferred_scenarios": len(scenario_memories["memories"]),
            "profile_details": profile_memories,
            "behavioral_details": behavioral_memories,
            "scenario_details": scenario_memories
        }

    def add_roleplay_memories_batch(self, facts_list, user_id):
        """批量添加角色扮演记忆 - 优化版本"""
        if not facts_list:
            return {"results": [], "added_count": 0}
        
        print(f"🎭 批量处理 {len(facts_list)} 条角色扮演记忆...")
        start_time = time.time()
        
        # 批量处理记忆
        try:
            # 构建批量消息
            batch_messages = []
            for fact in facts_list:
                metadata = {
                    "category": fact["category"],
                    "importance": fact["importance"], 
                    "classification_reasoning": fact.get("reasoning", "auto_classified"),
                    "memory_type": "long_term" if fact["importance"] in ["high", "medium"] else "short_term",
                    "roleplay_context": True,
                    "auto_classified": True
                }
                
                batch_messages.append({
                    "content": fact["content"],
                    "user_id": user_id,
                    "metadata": metadata
                })
            
            # 批量添加到向量存储
            results = self._batch_add_to_vector_store(batch_messages)
            
            total_time = time.time() - start_time
            added_count = len([r for r in results if r.get('event') == 'ADD'])
            
            print(f"✅ 批量处理完成: {added_count} 条新增，总耗时: {total_time:.2f}s")
            
            return {
                "results": results,
                "added_count": added_count,
                "total_time": total_time
            }
            
        except Exception as e:
            print(f"❌ 批量处理失败: {e}")
            return {"results": [], "added_count": 0}

    def _batch_add_to_vector_store(self, batch_messages, infer=True):
        """批量添加到向量存储 - 参考mem0但支持批量LLM处理"""
        if not infer:
            # 如果不推理，直接添加
            return self._batch_add_directly(batch_messages)
        
        # 批量LLM推理
        return self._batch_infer_and_add(batch_messages)

    def _batch_infer_and_add(self, batch_messages, batch_size=5):
        """批量LLM推理和添加"""
        all_results = []
        
        # 分批处理，避免一次处理太多
        for i in range(0, len(batch_messages), batch_size):
            batch = batch_messages[i:i + batch_size]
            print(f"🔍 处理批次 {i//batch_size + 1}: {len(batch)} 条记忆")
            
            # 构建批量提示词
            batch_prompt = self._create_batch_inference_prompt(batch)
            
            # 调用LLM进行批量推理
            batch_results = self._batch_llm_inference(batch_prompt, batch)
            all_results.extend(batch_results)
        
        return all_results

    def _create_batch_inference_prompt(self, batch_messages):
        """创建批量推理提示词"""
        memory_list = []
        for i, msg in enumerate(batch_messages, 1):
            memory_list.append(f"{i}. 内容: {msg['content']}")
            memory_list.append(f"   元数据: 分类={msg['metadata'].get('category')}, 重要性={msg['metadata'].get('importance')}")
            memory_list.append("")
        
        prompt = f"""你是一个记忆管理系统，需要判断以下记忆是否需要添加、更新或删除。

    ## 现有记忆分析规则：
    1. **ADD（新增）**: 如果记忆内容全新且与现有记忆不重复
    2. **UPDATE（更新）**: 如果记忆与现有记忆相似但包含新信息
    3. **DELETE（删除）**: 如果记忆与现有记忆完全重复或信息过时
    4. **NOOP（无操作）**: 如果记忆质量差或无法处理

    ## 待处理记忆列表：
    {"\n".join(memory_list)}

    ## 输出要求：
    请按以下JSON格式返回处理结果：
    {{
    "results": [
        {{
        "index": 1,
        "content": "原始内容",
        "event": "ADD/UPDATE/DELETE/NOOP",
        "reasoning": "处理理由",
        "updated_content": "如果是UPDATE，提供更新后的内容"
        }}
    ]
    }}

    请基于记忆内容和元数据进行智能判断。"""
        
        return prompt

    def _batch_llm_inference(self, prompt, batch_messages):
        """批量LLM推理"""
        try:
            from openai import OpenAI
            import json
            
            client = OpenAI(
                base_url=config.get_llm_config()["config"]["openai_base_url"],
                api_key=config.get_llm_config()["config"]["api_key"]
            )
            
            response = client.chat.completions.create(
                model=config.get_llm_config()["config"]["model"],
                messages=[
                    {
                        "role": "system", 
                        "content": "你是记忆管理专家，负责批量处理记忆的添加、更新和删除。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # 将LLM结果转换为mem0格式
            formatted_results = []
            for item in result.get("results", []):
                index = item.get("index", 1) - 1  # 转换为0-based索引
                if 0 <= index < len(batch_messages):
                    original_msg = batch_messages[index]
                    formatted_results.append({
                        "id": f"batch_{index}",
                        "memory": item.get("content", original_msg["content"]),
                        "event": item.get("event", "ADD"),
                        "metadata": original_msg["metadata"],
                        "reasoning": item.get("reasoning", "")
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ 批量LLM推理失败: {e}")
            # 失败时默认全部添加
            return self._batch_add_directly(batch_messages)

    def _batch_add_directly(self, batch_messages):
        """直接批量添加（无推理）"""
        results = []
        for msg in batch_messages:
            try:
                # 使用mem0的直接添加
                result = self.memory.add(
                    msg["content"],
                    user_id=msg["user_id"],
                    metadata=msg["metadata"],
                    infer=False
                )
                results.extend(result.get("results", []))
            except Exception as e:
                print(f"❌ 添加记忆失败: {e}")
        
        return results