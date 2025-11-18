from .smart_memory_manager import SmartMemoryManager
from .config import config
import time
import json

class RoleplaySmartMemoryManager(SmartMemoryManager):
    """角色扮演专用的智能记忆管理器 - 完整版"""
    
    def __init__(self, memory_client=None):
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
        
        # 添加记忆到系统
        added_count = 0
        for fact in classified_facts["facts"]:
            metadata = {
                "category": fact["category"],
                "importance": fact["importance"], 
                "classification_reasoning": fact.get("reasoning", "auto_classified"),
                "memory_type": "long_term" if fact["importance"] in ["high", "medium"] else "short_term",
                "roleplay_context": True,
                "auto_classified": True
            }
            
            try:
                self.memory.add(fact["content"], user_id=user_id, metadata=metadata,infer=False)
                added_count += 1
            except Exception as e:
                print(f"❌ 添加记忆失败: {e}")
        
        total_time = time.time() - start_time
        print(f"✅ 角色扮演记忆添加完成: {added_count} 条，总耗时: {total_time:.2f}s")
        
        return {
            "classified_facts": classified_facts,
            "added_count": added_count,
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