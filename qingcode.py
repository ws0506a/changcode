#!/usr/bin/env python3
"""
QingCode - 由开源大模型驱动的AI编程助手
类似 Claude Code，但使用国产开源模型
"""

import os
import sys
import argparse
from pathlib import Path

from config import QingCodeConfig, load_config, PRESET_CONFIGS
from terminal import Terminal
from agent import Agent


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="QingCode - AI编程助手",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  qingcode                          # 启动交互模式
  qingcode -p "帮我写一个排序算法"    # 单次查询
  qingcode --model deepseek-coder   # 使用特定模型
  qingcode --api-key sk-xxx         # 指定API密钥
  qingcode --base-url http://...    # 指定API地址
        """
    )

    parser.add_argument("-p", "--prompt", help="单次查询模式")
    parser.add_argument("--model", help="模型名称")
    parser.add_argument("--provider", choices=["deepseek", "openai", "anthropic"], 
                       help="模型提供商")
    parser.add_argument("--api-key", help="API密钥")
    parser.add_argument("--base-url", help="API地址")
    parser.add_argument("--temperature", type=float, help="温度参数")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--auto-confirm", "-y", action="store_true", 
                       help="自动确认所有操作")
    parser.add_argument("--version", action="version", version="QingCode 1.0.0")

    args = parser.parse_args()

    # 加载配置
    config = load_config()

    # 应用命令行参数
    if args.model:
        config.llm.model = args.model
    if args.provider:
        config.llm.provider = args.provider
    if args.api_key:
        config.llm.api_key = args.api_key
    if args.base_url:
        config.llm.base_url = args.base_url
    if args.temperature is not None:
        config.llm.temperature = args.temperature
    if args.verbose:
        config.agent.verbose = True
    if args.auto_confirm:
        config.agent.auto_confirm = True

    # 检查 API Key
    if not config.llm.api_key:
        config.llm.api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        
        if not config.llm.api_key:
            print("错误: 未设置 API Key")
            print("请通过以下方式之一设置:")
            print("  1. 设置环境变量: export DEEPSEEK_API_KEY=your-key")
            print("  2. 命令行参数: qingcode --api-key your-key")
            print("  3. 在 ~/.qingcode/config.json 中配置")
            sys.exit(1)

    # 设置默认 base_url (DeepSeek)
    if not config.llm.base_url and config.llm.provider == "deepseek":
        config.llm.base_url = "https://api.deepseek.com/v1"

    # 运行
    try:
        if args.prompt:
            # 单次查询模式
            agent = Agent(config)
            response = agent.chat(args.prompt)
            print(response)
        else:
            # 交互模式
            terminal = Terminal(config)
            terminal.run()
    except KeyboardInterrupt:
        print("\n再见！")
    except Exception as e:
        print(f"错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
