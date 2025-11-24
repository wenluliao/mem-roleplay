import time
import json
import re
from h11 import Data
from openai import OpenAI
from .smart_memory_manager import SmartMemoryManager
from .config import config
from .redis_memory_queue import RedisMemoryQueue

class RoleplaySmartMemoryManager(SmartMemoryManager):
    """角色扮演专用的智能记忆管理器 - 优化完整版"""
    
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
        self._processing_started = False
        
        if use_async:
            print("🔄 启用异步处理模式")
            self.async_processor = RedisMemoryQueue(self)
            import threading
            if not self._processing_started:
                self.process_thread = threading.Thread(
                    target=self.async_processor.start_processing, 
                    daemon=True
                )
                self.process_thread.start()
                self._processing_started = True
    
    def add_conversation_with_roleplay_classification(self, messages, user_id):
        """
        使用角色扮演分类添加对话
        """
        user_messages = messages
        
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
                "updated_count": result.get("updated_count", 0),
                "stats": result.get("stats", {}),
                "total_time": total_time
            }

    def _extract_roleplay_facts(self, user_messages):
        """提取角色扮演专用事实 - 保留完整对话上下文"""
        try:
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

        ### 🎭 roleplay_scenarios (扮演场景) - 剧情偏好
        - 用户喜欢的题材和剧情类型
        - 用户偏好的场景设定和情节
        - 用户想体验的角色和情境
        - *重要性：low*

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
        """调用LLM进行角色扮演分类 - 兼容各种格式的响应"""
        try:
            print("🤖 正在调用LLM进行角色扮演分类...")
            
            client = OpenAI(
                base_url=config.get_llm_config()["config"]["openai_base_url"],
                api_key=config.get_llm_config()["config"]["api_key"]
            )
            
            response = client.chat.completions.create(
                model=config.get_llm_config()["config"]["model"],
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的角色扮演记忆分类专家，请严格按照要求的JSON格式返回结果，不要添加任何额外的格式标记、代码块符号或解释文字。"
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
            
            response_content = response.choices[0].message.content
            print(f"📄 LLM原始响应: {response_content}")
            
            result = self._parse_llm_response(response_content)
            
            if result and "facts" in result and isinstance(result["facts"], list):
                print(f"✅ LLM分类成功，提取到 {len(result['facts'])} 条事实")
                return result
            else:
                print("❌ LLM返回格式不正确或解析失败")
                return {"facts": []}
                
        except Exception as e:
            print(f"❌ LLM调用失败: {e}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
            return {"facts": []}

    def _parse_llm_response(self, response_content):
        """解析LLM响应，兼容多种格式"""
        import json
        
        # 如果响应已经是干净的JSON，直接解析
        try:
            return json.loads(response_content)
        except json.JSONDecodeError:
            pass
        
        # 方法1: 提取代码块中的JSON
        code_block_patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
        ]
        
        for pattern in code_block_patterns:
            match = re.search(pattern, response_content, re.DOTALL)
            if match:
                try:
                    json_str = match.group(1).strip()
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue
        
        # 方法2: 提取最外层的大括号内容
        brace_pattern = r'\{.*\}'
        match = re.search(brace_pattern, response_content, re.DOTALL)
        if match:
            try:
                json_str = match.group(0).strip()
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # 方法3: 手动清理和修复常见的格式问题
        cleaned_content = response_content
        
        prefixes_to_remove = [
            "以下是分类结果：",
            "分类结果：",
            "结果：",
            "根据对话内容，我提取了以下事实：",
        ]
        
        suffixes_to_remove = [
            "以上是根据对话内容提取的事实。",
            "希望这个分类结果对您有帮助。",
            "这就是我的分析结果。",
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned_content.startswith(prefix):
                cleaned_content = cleaned_content[len(prefix):].strip()
        
        for suffix in suffixes_to_remove:
            if cleaned_content.endswith(suffix):
                cleaned_content = cleaned_content[:-len(suffix)].strip()
        
        # 再次尝试解析清理后的内容
        try:
            return json.loads(cleaned_content)
        except json.JSONDecodeError:
            pass
        
        print(f"❌ 无法解析LLM响应: {response_content}")
        return None

    def add_roleplay_memories_batch(self, facts_list, user_id):
        """增强版批量添加角色扮演记忆 - 包含性能监控"""
        if not facts_list:
            return {"results": [], "added_count": 0}
        
        print(f"🎭 批量处理 {len(facts_list)} 条角色扮演记忆...")
        start_time = time.time()
        
        # 性能监控
        stats = {
            "total_memories": len(facts_list),
            "processing_start": start_time,
            "batch_processing_time": 0,
            "llm_inference_time": 0,
            "vector_store_time": 0
        }
        
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
                    "auto_classified": True,
                    "timestamp": time.time()
                }
                
                batch_messages.append({
                    "content": fact["content"],
                    "user_id": user_id,
                    "metadata": metadata
                })
            
            # 批量推理
            inference_start = time.time()
            results = self._smart_batch_processing(batch_messages, user_id)
            stats["llm_inference_time"] = time.time() - inference_start
            
            # 执行实际操作
            store_start = time.time()
            actual_results = self._execute_batch_operations(results, user_id)
            stats["vector_store_time"] = time.time() - store_start
            
            total_time = time.time() - start_time
            stats["batch_processing_time"] = total_time
            
            added_count = len([r for r in actual_results if r.get('event') == 'ADD'])
            updated_count = len([r for r in actual_results if r.get('event') == 'UPDATE'])
            
            print(f"✅ 批量处理完成: {added_count}新增, {updated_count}更新, 总耗时: {total_time:.2f}s")
            self._print_performance_stats(stats)
            
            return {
                "results": actual_results,
                "stats": stats,
                "added_count": added_count,
                "updated_count": updated_count,
                "total_time": total_time
            }
            
        except Exception as e:
            print(f"❌ 批量处理失败: {e}")
            return {"results": [], "added_count": 0, "error": str(e)}

    def _smart_batch_processing(self, batch_messages, user_id, batch_size=8):
        """智能批量处理 - 根据记忆特性动态分组"""
        
        # 按分类和重要性分组，提高处理效率
        categorized_batches = self._categorize_memories_for_batching(batch_messages)
        
        all_results = []
        
        relevance_groups = []

        for category, memories in categorized_batches.items():
            print(f"🔄 处理 {category} 分类的记忆: {len(memories)} 条")
            
            # 对每个分类内的记忆进一步按相关性分组
            relevance_groups.extend(self._group_memories_by_relevance(memories))
            
        # for group in relevance_groups:
        batch_results = self._process_batch_with_llm(relevance_groups, user_id)
        all_results.extend(batch_results)
        
        return all_results

    def _categorize_memories_for_batching(self, memories):
        """按分类和重要性对记忆进行分组"""
        categories = {}
        
        for memory in memories:
            metadata = memory['metadata']
            category = metadata.get('category', 'unknown')
            importance = metadata.get('importance', 'medium')
            
            # 创建分类键
            category_key = f"{category}_{importance}"
            
            if category_key not in categories:
                categories[category_key] = []
            categories[category_key].append(memory)
        
        return categories

    def _group_memories_by_relevance(self, memories, similarity_threshold=0.7):
        """根据内容相似性对记忆分组"""
        if len(memories) <= 1:
            return [memories]
        
        # 基于关键词的相似性分组
        groups = []
        
        for memory in memories:
            content = memory['content']
            placed = False
            
            for group in groups:
                if self._calculate_content_similarity(content, group[0]['content']) > similarity_threshold:
                    group.append(memory)
                    placed = True
                    break
            
            if not placed:
                groups.append([memory])
        
        return groups

    def _calculate_content_similarity(self, text1, text2):
        """计算内容相似度（简化版）"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)

    def _process_batch_with_llm(self, batch_messages, user_id):
        """使用LLM处理批量记忆"""
        if not batch_messages:
            return []
        
        # 构建批量提示词
        batch_prompt = self._create_batch_inference_prompt(batch_messages, user_id)
        
        # 调用增强的LLM推理
        return self._enhanced_llm_inference(batch_prompt, batch_messages)

    def _create_batch_inference_prompt(self, group, user_id):
        """创建批量推理提示词 - 集成现有记忆检索"""
        
        # 1. 为批量中的每条记忆检索相关现有记忆
        existing_memories_map = self._retrieve_existing_memories_for_batch(group, user_id)
        
        # 2. 构建记忆列表，包含索引和相关的现有记忆
        index = 0
        memory_entries = []
        for batch_messages in group:
            for i, msg in enumerate(batch_messages, 1):
                memory_entries.append({
                    "index": i,
                    "content": msg['content'],
                    "metadata": msg['metadata'],
                    "existing_memories": existing_memories_map.get(index, [])
                })
                index += 1
        
        prompt = f"""# 记忆批量处理专家

    ## 任务说明
    您需要综合分析以下{len(memory_entries)}条新记忆，并与现有记忆库进行比较，判断每条记忆应该执行的操作。

    ## 处理规则
    - **ADD（新增）**: 记忆内容全新且与现有记忆库不重复
    - **UPDATE（更新）**: 与现有记忆相似但包含重要新信息或修正，需要更新
    - **DELETE（删除）**: 与现有记忆完全重复或信息已过时无效  
    - **MERGE（合并）**: 与现有多条记忆相似但包含重要新信息或修正，需要合并并更新  
    - **NOOP（无操作）**: 记忆质量差、无法处理或无需记录

    ## 综合分析指南
    请特别关注：
    1. **新旧记忆关联性** - 新记忆是否与现有记忆描述同一主题
    2. **信息互补性** - 新记忆是否包含可以补充现有记忆的信息
    3. **冲突检测** - 新记忆是否与现有记忆存在矛盾
    4. **重要性层级** - 高重要性记忆优先保留和更新

    ## 待处理新记忆列表（与相关现有记忆对比）
    {self._format_memory_list_with_existing(memory_entries)}

    ## 输出格式
    请严格按照以下JSON格式返回：
    {{
        "batch_analysis": "对这批记忆的整体分析说明",
        "cross_memory_insights": "新旧记忆间的关联性和合并建议", 
        "results": [
            {{
                "index": 1,
                "content": "原始内容",
                "event": "ADD/UPDATE/DELETE/MERGE/NOOP",
                "reasoning": "详细处理理由，包括与现有记忆的对比分析",
                "updated_content": "如果是UPDATE，提供合并优化后的内容",
                "merged_content": "如果是MERGE，提供合并后的内容",
                "related_existing_ids": ["需要更新或者合并的现有记忆ID列表"]
            }}
        ]
    }}"""

        return prompt

    def _retrieve_existing_memories_for_batch(self, group, user_id, top_k=3):
        """为批量中的每条记忆检索相关的现有记忆 - 仅相同分类"""
        existing_memories_map = {}
        
        index = 0
        for batch_messages in group:
            for i, msg in enumerate(batch_messages, 1):
                try:
                    content = msg['content']
                    category = msg["metadata"].get('category', 'unknown')
                    
                    # 调用mem0的搜索功能查找相关记忆
                    search_results = self.memory.search(
                        content, 
                        user_id=user_id, 
                        filters={"category": {"contains": category}},
                        limit=top_k,  # 多检索一些用于分类过滤
                        rerank=True
                    )
                    
                    # 仅保留相同分类的结果
                    filtered_results = []
                    for item in search_results.get('results', []):
                        item_metadata = item.get('metadata', {})
                        item_category = item_metadata.get('category', 'unknown')
                        
                        # 只保留相同分类且相关性高的记忆
                        if (item_category == category and item.get('score', 0) < 0.4):
                            filtered_results.append({
                                "id": item.get('id'),
                                "content": item.get('memory'),
                                "metadata": item_metadata,
                                "score": item.get('score', 0)
                            })
                    
                    # 按分数排序并限制数量
                    # filtered_results.sort(key=lambda x: x['score'])
                    # filtered_results = filtered_results[:top_k]
                    
                    print(f"原记忆 [{category}] '{content}' 找到 {len(filtered_results)} 条同分类记忆")
                    
                    existing_memories_map[index] = filtered_results

                    index += 1
                    
                except Exception as e:
                    print(f"检索现有记忆失败 (索引 {i}): {e}")
                    existing_memories_map[i] = []
        
        return existing_memories_map

    def _format_memory_list_with_existing(self, memory_entries):
        """格式化记忆列表，包含现有记忆对比"""
        formatted = []
        for entry in memory_entries:
            formatted.append(f"{entry['index']}. 新记忆内容: {entry['content']}")
            formatted.append(f"    元数据: 分类={entry['metadata'].get('category')}, 重要性={entry['metadata'].get('importance')}")
            
            # 添加相关现有记忆
            existing_memories = entry['existing_memories']
            if existing_memories:
                formatted.append("    相关现有记忆:")
                for existing in existing_memories:
                    formatted.append(f"      - ID: {existing['id']}")
                    formatted.append(f"        内容: {existing['content']}")
                    formatted.append(f"        相关性: {existing['score']:.3f}")
            else:
                formatted.append("    相关现有记忆: 无")
            
            formatted.append("")
        return "\n".join(formatted)

    def _format_memory_list_for_batch(self, memory_entries):
        """格式化记忆列表用于批量提示词"""
        formatted = []
        for entry in memory_entries:
            metadata = entry['metadata']
            formatted.append(f"{entry['index']}. 内容: {entry['content']}")
            formatted.append(f"    元数据: 分类={metadata.get('category')}, 重要性={metadata.get('importance')}")
            formatted.append("")
        return "\n".join(formatted)

    def _enhanced_llm_inference(self, prompt, batch_messages, max_retries=2):
        """增强的LLM推理，包含重试和降级处理"""
        
        for attempt in range(max_retries + 1):
            try:
                response = self._call_llm_api(prompt)
                
                # 尝试解析响应
                parsed_result = self._parse_batch_llm_response(response, batch_messages)
                
                if parsed_result and self._validate_batch_results(parsed_result, batch_messages):
                    return parsed_result
                else:
                    print(f"⚠️ LLM响应验证失败，尝试 {attempt + 1}/{max_retries + 1}")
                    
            except Exception as e:
                print(f"❌ LLM调用失败 (尝试 {attempt + 1}): {e}")
            
            # 最后一次尝试使用降级方案
            if attempt == max_retries:
                print("🔄 使用降级处理方案")
                return self._fallback_batch_processing(batch_messages)
        
        return []

    def _call_llm_api(self, prompt):
        """调用LLM API"""
        client = OpenAI(
            base_url=config.get_llm_config()["config"]["openai_base_url"],
            api_key=config.get_llm_config()["config"]["api_key"]
        )
        
        response = client.chat.completions.create(
            model=config.get_llm_config()["config"]["model"],
            messages=[
                {
                    "role": "system", 
                    "content": "你是记忆管理专家，负责批量处理记忆的添加、更新和删除。请严格按JSON格式返回结果。"
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
        
        return response.choices[0].message.content

    def _parse_batch_llm_response(self, response_content, batch_messages):
        """解析批量LLM响应，增强容错"""
        try:
            # 清理响应内容
            cleaned_content = self._clean_llm_response(response_content)
            result = json.loads(cleaned_content)
            
            # 验证基础结构
            if "results" not in result:
                return None
                
            # 处理每条结果
            processed_results = []
            for item in result["results"]:
                index = item.get("index", 1) - 1
                
                if 0 <= index < len(batch_messages):
                    original_msg = batch_messages[index]
                    
                    processed_result = {
                        "id": f"batch_{index}_{int(time.time())}",
                        "memory": item.get("content", original_msg[0]["content"]),
                        "event": item.get("event", "ADD"),
                        "metadata": original_msg[0]["metadata"],
                        "reasoning": item.get("reasoning", "自动处理"),
                        "related_existing_ids": item.get("related_existing_ids", []),
                        "batch_index": index
                    }
                    
                    # 如果是更新操作，添加更新后内容
                    if item.get("event") == "UPDATE" and item.get("updated_content"):
                        processed_result["updated_content"] = item["updated_content"]
                        
                    # 如果是合并操作，添加合并后内容
                    if item.get("event") == "MERGE" and item.get("merged_content"):
                        processed_result["merged_content"] = item["merged_content"]
                        
                    processed_results.append(processed_result)
            
            return processed_results
            
        except Exception as e:
            print(f"❌ 解析批量LLM响应失败: {e}")
            return None

    def _clean_llm_response(self, response):
        """清理LLM响应，移除可能的格式问题"""
        # 移除代码块标记
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        
        # 移除可能的XML标签
        response = re.sub(r'</?response>', '', response)
        
        # 提取最外层JSON对象
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        return response.strip()

    def _validate_batch_results(self, results, batch_messages):
        """验证批量处理结果"""
        if not results:
            return False
        
        # 检查结果数量是否匹配
        if len(results) != len(batch_messages):
            print(f"⚠️ 结果数量不匹配: 预期{len(batch_messages)}，实际{len(results)}")
            return False
        
        # 检查每个结果的基本字段
        for result in results:
            if not all(key in result for key in ['memory', 'event', 'reasoning']):
                print("⚠️ 结果缺少必要字段")
                return False
        
        return True

    def _fallback_batch_processing(self, batch_messages):
        """降级处理方案 - 默认全部添加"""
        results = []
        for i, msg in enumerate(batch_messages):
            results.append({
                "id": f"fallback_{i}_{int(time.time())}",
                "memory": msg["content"],
                "event": "ADD",
                "metadata": msg["metadata"],
                "reasoning": "降级处理：默认添加",
                "batch_index": i
            })
        return results

    def _execute_batch_operations(self, results, user_id):
        """执行批量操作"""
        actual_results = []
        
        for result in results:
            try:
                event = result.get("event", "ADD")
                
                if event == "ADD":
                    # 添加新记忆
                    add_result = self.memory.add(
                        result["memory"],
                        user_id=user_id,
                        metadata=result["metadata"],
                        infer=False
                    )
                    actual_results.extend(add_result.get("results", []))
                    
                elif event == "UPDATE":
                    # 更新现有记忆（这里需要根据您的记忆系统实现更新逻辑）
                    # 假设您的记忆系统支持更新操作
                    updated_content = result.get("updated_content", result["memory"])
                    update_result = self.memory.update(
                        memory_id=result["related_existing_ids"][0],  # 需要现有记忆的ID
                        data=updated_content
                    )
                    actual_results.extend(update_result.get("results", []))

                elif event == "MERGE":
                    # 合并现有记忆（这里需要根据您的记忆系统实现合并逻辑）
                    merged_content = result.get("merged_content", result["memory"])
                    # 添加新记忆
                    merge_result = self.memory.add(
                        merged_content,
                        user_id=user_id,
                        metadata=result["metadata"],
                        infer=False
                    )
                    # 删除需要合并的记忆
                    for memory_id in result["related_existing_ids"]:
                            delete_result = self.memory.delete(memory_id)
                    actual_results.extend(merge_result.get("results", []))
                    
                elif event == "DELETE":
                    # 删除重复记忆 - 保留一个，删除其他重复项
                    if result.get("related_existing_ids") and len(result["related_existing_ids"]) > 1:
                        # 保留第一个记忆，删除其他重复的记忆
                        for memory_id in result["related_existing_ids"][1:]:
                            delete_result = self.memory.delete(memory_id)
                            actual_results.extend(delete_result.get("results", []))
                        print(f"✅ 删除重复记忆完成：保留1个，删除{len(result['related_existing_ids']) - 1}个")
                
            except Exception as e:
                print(f"❌ 执行{event}操作失败: {e}")
                # 记录失败的操作
                actual_results.append({
                    "event": f"FAILED_{event}",
                    "error": str(e),
                    "content": result.get("memory", "")
                })
        
        return actual_results

    def _print_performance_stats(self, stats):
        """打印性能统计"""
        print("📊 批量处理性能统计:")
        print(f"  - 总记忆数: {stats['total_memories']}")
        print(f"  - LLM推理时间: {stats['llm_inference_time']:.2f}s")
        print(f"  - 向量存储时间: {stats['vector_store_time']:.2f}s")
        print(f"  - 总处理时间: {stats['batch_processing_time']:.2f}s")
        
        if stats['batch_processing_time'] > 0:
            efficiency = stats['total_memories'] / stats['batch_processing_time']
            print(f"  - 处理效率: {efficiency:.2f} 条/秒")

    # 保留原有的工具方法
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

    def search_roleplay_memories(self, user_id: str, query: str, category: str = None, agent_id: str = None, limit: int = 10):
        """搜索角色扮演记忆"""
        try:
            print(f"🔍 搜索角色扮演记忆: 用户={user_id}, 查询='{query}', 分类={category}")
            
            search_results = self.search_smart(query, user_id, category=category, agent_id=agent_id, limit=limit, exclude_deleted=True)["results"]
            
            print(f"✅ 搜索完成: 找到 {len(search_results)} 条角色扮演记忆")
            return search_results
            
        except Exception as e:
            print(f"❌ 搜索角色扮演记忆失败: {e}")
            return []

    def get_memories(self, user_id: str, category: str = None, limit: int = 100):
        """获取所有角色扮演记忆（按分类过滤）"""
        try:
            print(f"📊 获取角色扮演记忆: 用户={user_id}, 分类={category or 'all'}")
            
            # 获取所有记忆
            all_memories = []
            if category:
                all_memories = self.memory.get_all(
                    user_id=user_id,
                    filters={"category": {"contains": category}}
                )["results"]
            else:
                all_memories = self.get_all_memories(user_id)["results"]
            
            
            # 按时间排序（最新的在前）
            all_memories.sort(key=lambda x: x.get('timestamp', 0) or x.get('created_at', 0), reverse=True)
            
            print(f"✅ 获取完成: 找到 {len(all_memories)} 条角色扮演记忆")
            return all_memories
            
        except Exception as e:
            print(f"❌ 获取角色扮演记忆失败: {e}")
            return []