"""
性能优化测试
"""

import os
import sys
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.app import Mem0App

def test_optimized_roleplay():
    """测试优化后的角色扮演性能"""
    print("=== 优化版角色扮演性能测试 ===\n")
    
    app = Mem0App()
    
    # 测试数据
    roleplay_messages = [
        {"role": "user", "content": "我是来自森林的精灵弓箭手，擅长自然魔法"},
        {"role": "assistant", "content": "很高兴认识你，精灵朋友！你的弓箭一定很厉害吧"},
        {"role": "user", "content": "是的，我可以用魔法箭矢。其实我有点害怕人类，但觉得你还不错"},
        {"role": "assistant", "content": "不用害怕，我会保护你的"},
        {"role": "user", "content": "我喜欢在月光下散步，感受自然的气息。我们精灵族对金属过敏，不能接触铁器"},
        {"role": "assistant", "content": "明白了，我会注意不让你接触金属物品"},
        {"role": "user", "content": "要不下次我们在森林深处见面吧，那里有我的秘密基地"}
    ]
    
    start_time = time.time()
    
    try:
        result = app.add_conversation(roleplay_messages, user_id="optimized_test", 
                                    enable_roleplay_classification=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ 总耗时: {duration:.2f}秒")
        print(f"📊 添加记忆数量: {result.get('added_count', '未知')}")
        
        # 性能标准：应该在30秒内完成
        if duration < 30:
            print("✅ 性能优化成功！")
        else:
            print("⚠️ 性能仍需优化")
            
        return duration < 30
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_memory_stats():
    """测试记忆统计"""
    print("\n=== 记忆统计测试 ===\n")
    
    app = Mem0App()
    
    try:
        stats = app.get_memory_stats("optimized_test")
        print(f"总记忆数量: {stats['total_memories']}")
        print(f"活跃记忆: {stats['active_memories']}")
        
        # 测试分类搜索
        profile_results = app.search_by_category("profile", "optimized_test")
        print(f"档案类记忆: {profile_results['total_count']} 条")
        
        return True
        
    except Exception as e:
        print(f"❌ 统计测试失败: {e}")
        return False

if __name__ == "__main__":
    print("开始性能优化测试...\n")
    
    test1 = test_optimized_roleplay()
    test2 = test_memory_stats()
    
    print(f"\n{'='*50}")
    if test1 and test2:
        print("🎉 性能优化测试通过！")
        print("现在可以重新运行完整的角色扮演测试了。")
    else:
        print("💥 性能优化需要进一步调整")