"""
Mem0AI Web服务启动脚本
"""
import os
import sys
import argparse
from pathlib import Path

# 加载.env文件
from dotenv import load_dotenv
load_dotenv()

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Mem0AI Web服务启动脚本")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址 (默认: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="监听端口 (默认: 8000)")
    parser.add_argument("--reload", action="store_true", help="启用热重载")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    
    args = parser.parse_args()
    
    print("🚀 启动 Mem0AI 角色扮演记忆Web服务")
    print(f"📡 服务地址: http://{args.host}:{args.port}")
    print(f"🔧 热重载: {'启用' if args.reload else '禁用'}")
    print(f"🐛 调试模式: {'启用' if args.debug else '禁用'}")
    print("-" * 50)
    
    # 设置环境变量
    if args.debug:
        os.environ["LOG_LEVEL"] = "DEBUG"
    
    # 导入并运行Web服务
    from src.web_service import run_web_service
    
    run_web_service(
        host=args.host,
        port=args.port,
        reload=args.reload
    )

if __name__ == "__main__":
    main()