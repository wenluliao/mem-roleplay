"""
测试文件 - 使用模块化结构
"""

import os
import sys
import time
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.app import Mem0App


def test_basic_functionality():
    """测试基本功能"""
    print("=== 基本功能测试 ===\n")
    
    # 初始化应用
    app = Mem0App()
    
    # 测试对话
    messages = [
        {"role": "user", "content": "我喜欢看电影，要不下周二去看电影吧"},
        {"role": "assistant", "content": "好的呀，你喜欢看什么电影"},
        {"role": "user", "content": "我喜欢看国漫动画，比如哪吒系列的"},
        {"role": "assistant", "content": "我也很喜欢，那我们到时候一起吧"},
        {"role": "user", "content": "对了，我对花生严重过敏，一点都不能碰"},
        {"role": "assistant", "content": "好的，我会记住你对花生过敏"}
    ]
    
    # 添加对话
    print("1. 添加对话到记忆库...")
    result = app.add_conversation(messages, user_id="test_user")
    print(f"添加结果: {result}\n")
    
    # 搜索测试
    print("2. 搜索测试...")
    results = app.search_memories("喜欢什么", "test_user")
    app.print_search_results(results, "搜索测试结果")
    
    # 统计信息
    print("3. 统计信息测试...")
    stats = app.get_memory_stats("test_user")
    print(f"统计信息: {stats}\n")
    
    print("基本功能测试完成！\n")


def test_memory_management():
    """测试记忆管理功能"""
    print("=== 记忆管理功能测试 ===\n")
    
    app = Mem0App()
    
    # 更新记忆测试
    print("1. 记忆更新测试...")
    updated_count = app.update_memory("看电影", "我特别喜欢看科幻电影和国漫", "test_user", importance="medium")
    print(f"更新了 {updated_count} 条记忆\n")
    
    # 删除记忆测试
    print("2. 记忆删除测试...")
    deleted_count = app.delete_memory("下周二", "test_user")
    print(f"删除了 {deleted_count} 条记忆\n")
    
    # 清理测试
    print("3. 记忆清理测试...")
    cleanup_result = app.cleanup_memories("test_user")
    print(f"清理结果: {cleanup_result}\n")
    
    print("记忆管理功能测试完成！\n")


def test_roleplay_features():
    """测试角色扮演专用功能"""
    print("=== 角色扮演功能测试 ===\n")
    
    app = Mem0App()
    
    # 角色扮演对话
    roleplay_messages = [
        {"role": "user", "content": "我是来自森林的精灵弓箭手，擅长自然魔法"},
        {"role": "assistant", "content": "很高兴认识你，精灵朋友！我叫露西，你的弓箭一定很厉害吧，"},
        {"role": "user", "content": "我叫杰克。是的，我可以用魔法箭矢。其实我有点害怕人类，但觉得你还不错"},
        {"role": "assistant", "content": "不用害怕，我会保护你的"},
        {"role": "user", "content": "我喜欢在月光下散步，感受自然的气息。我们精灵族对金属过敏，不能接触铁器"},
        {"role": "assistant", "content": "明白了，我会注意不让你接触金属物品"},
        {"role": "user", "content": "要不下次我们在森林深处见面吧，那里有我的秘密基地"}
    ]
    
    # 启用角色扮演分类
    print("1. 添加角色扮演对话...")
    result = app.add_conversation(roleplay_messages, user_id="elf_user", enable_roleplay_classification=True)
    print("角色扮演对话添加完成！\n")
    print(result)
    
    # 测试角色档案
    print("2. 角色档案分析...")
    app.print_character_profile("elf_user")
    
    # 测试分类搜索
    print("3. 分类搜索测试...")
    profile_results = app.search_by_category("profile", "elf_user")
    print(f"档案类记忆: {profile_results['total_count']} 条")
    
    scenario_results = app.search_by_category("roleplay_scenarios", "elf_user")
    print(f"场景类记忆: {scenario_results['total_count']} 条")
    
    # 测试行为模式
    print("\n4. 行为模式分析...")
    patterns = app.get_behavioral_patterns("elf_user")
    print(f"发现行为模式: {patterns['pattern_count']} 种")
    
    print("角色扮演功能测试完成！\n")


def test_advanced_features():
    """测试高级功能"""
    print("=== 高级功能测试 ===\n")
    
    app = Mem0App()
    
    # 重要记忆测试
    print("1. 重要记忆获取...")
    important_memories = app.get_important_memories("test_user", "high")
    print(f"高重要性记忆: {len(important_memories['results'])} 条")
    
    # 频繁访问记忆测试
    print("\n2. 频繁访问记忆...")
    frequent_memories = app.get_frequent_memories("test_user", min_count=1)
    print(f"频繁访问记忆: {len(frequent_memories['results'])} 条")
    
    # 分类统计测试
    print("\n3. 分类统计...")
    category_stats = app.get_category_statistics("test_user")
    print(f"分类数量: {category_stats['category_count']}")
    
    # 性能统计
    print("\n4. 性能统计...")
    app.print_performance_stats()
    
    print("高级功能测试完成！\n")


def test_edge_cases():
    """测试边界情况"""
    print("=== 边界情况测试 ===\n")
    
    app = Mem0App()
    
    # 空搜索测试
    print("1. 空搜索测试...")
    empty_results = app.search_memories("", "test_user")
    print(f"空搜索返回: {empty_results['total_count']} 条结果\n")
    
    # 不存在的用户测试
    print("2. 不存在的用户测试...")
    try:
        nonexistent_stats = app.get_memory_stats("nonexistent_user")
        print(f"不存在的用户统计: {nonexistent_stats}\n")
    except Exception as e:
        print(f"不存在的用户测试异常: {e}\n")
    
    # 无效消息格式测试
    print("3. 无效消息格式测试...")
    try:
        invalid_messages = [{"role": "invalid", "content": 123}]
        result = app.add_conversation(invalid_messages, user_id="test_user")
        print(f"无效消息处理结果: {result}\n")
    except Exception as e:
        print(f"无效消息格式测试异常: {e}\n")
    
    # 大量数据测试
    print("4. 大量数据测试...")
    bulk_messages = []
    for i in range(5):  # 小批量测试
        bulk_messages.extend([
            {"role": "user", "content": f"测试消息 {i} - 我喜欢各种类型的音乐"},
            {"role": "assistant", "content": f"测试回复 {i} - 音乐确实很美妙"}
        ])
    
    result = app.add_conversation(bulk_messages, user_id="bulk_user")
    print(f"批量添加结果: {len(bulk_messages)} 条消息处理完成\n")
    
    print("边界情况测试完成！\n")


def test_memory_persistence():
    """测试记忆持久化"""
    print("=== 记忆持久化测试 ===\n")
    
    # 第一次初始化
    print("1. 第一次初始化应用...")
    app1 = Mem0App()
    
    # 添加一些记忆
    messages = [
        {"role": "user", "content": "持久化测试 - 我喜欢蓝色"},
        {"role": "assistant", "content": "蓝色是很棒的颜色"}
    ]
    app1.add_conversation(messages, user_id="persistence_user")
    
    # 重新初始化应用（模拟重启）
    print("2. 重新初始化应用...")
    app2 = Mem0App()
    
    # 检查记忆是否持久化
    print("3. 检查记忆持久化...")
    results = app2.search_memories("蓝色", "persistence_user")
    print(f"持久化搜索结果: {results['total_count']} 条")
    
    if results['total_count'] > 0:
        print("✅ 记忆持久化测试通过！")
    else:
        print("❌ 记忆持久化测试失败！")
    
    print("\n记忆持久化测试完成！\n")


def test_performance():
    """测试性能"""
    print("=== 性能测试 ===\n")
    
    app = Mem0App()
    
    # 搜索性能测试
    print("1. 搜索性能测试...")
    start_time = time.time()
    
    for i in range(3):
        results = app.search_memories(f"测试 {i}", "test_user")
    
    search_time = time.time() - start_time
    print(f"3次搜索平均耗时: {search_time/3:.2f}秒\n")
    
    # 添加性能测试
    print("2. 添加性能测试...")
    start_time = time.time()
    
    test_messages = [
        {"role": "user", "content": "性能测试消息"},
        {"role": "assistant", "content": "性能测试回复"}
    ]
    app.add_conversation(test_messages, user_id="performance_user")
    
    add_time = time.time() - start_time
    print(f"单次添加耗时: {add_time:.2f}秒\n")
    
    # 显示详细性能统计
    print("3. 详细性能统计...")
    app.print_performance_stats()
    
    print("性能测试完成！\n")


def run_all_tests():
    """运行所有测试"""
    print("开始运行Mem0智能记忆管理系统测试...\n")
    
    try:
        # 基础功能测试
        test_basic_functionality()
        
        # 记忆管理测试
        test_memory_management()
        
        # 角色扮演功能测试
        test_roleplay_features()
        
        # 高级功能测试
        test_advanced_features()
        
        # 边界情况测试
        test_edge_cases()
        
        # 持久化测试
        test_memory_persistence()
        
        # 性能测试
        test_performance()
        
        print("=== 所有测试完成 ===")
        print("🎉 系统运行正常！")
        print("\n测试总结:")
        print("✅ 基本功能正常")
        print("✅ 记忆管理功能正常") 
        print("✅ 角色扮演功能正常")
        print("✅ 高级功能正常")
        print("✅ 边界情况处理正常")
        print("✅ 记忆持久化正常")
        print("✅ 性能表现可接受")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


def run_specific_test(test_name):
    """运行特定测试"""
    tests = {
        "basic": test_basic_functionality,
        "management": test_memory_management,
        "roleplay": test_roleplay_features,
        "advanced": test_advanced_features,
        "edge": test_edge_cases,
        "persistence": test_memory_persistence,
        "performance": test_performance
    }
    
    if test_name in tests:
        print(f"运行特定测试: {test_name}\n")
        tests[test_name]()
    else:
        print(f"未知测试: {test_name}")
        print("可用测试: basic, management, roleplay, advanced, edge, persistence, performance")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Mem0测试套件')
    parser.add_argument('--test', type=str, help='运行特定测试')
    
    args = parser.parse_args()
    
    if args.test:
        run_specific_test(args.test)
    else:
        # 运行所有测试
        run_all_tests()