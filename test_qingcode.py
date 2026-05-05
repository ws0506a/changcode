#!/usr/bin/env python3
"""
QingCode 测试脚本
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import QingCodeConfig, LLMConfig, ToolConfig
from tools import ToolSystem, ToolResult
from llm import create_llm, OpenAILLM


def test_tool_system():
    """测试工具系统"""
    print("=" * 50)
    print("测试工具系统")
    print("=" * 50)

    tools = ToolSystem()

    # 测试获取当前目录
    print("\n[测试] get_current_dir")
    result = tools.execute("get_current_dir", {})
    print(f"  结果: {result.success}, 输出: {result.output[:50]}")

    # 测试列出目录
    print("\n[测试] list_directory")
    result = tools.execute("list_directory", {"path": "."})
    print(f"  结果: {result.success}")
    print(f"  输出预览: {result.output[:100]}...")

    # 测试搜索文件
    print("\n[测试] search_files")
    result = tools.execute("search_files", {"pattern": "*.py"})
    print(f"  结果: {result.success}")
    print(f"  输出: {result.output[:100]}...")

    # 测试写入和读取文件
    print("\n[测试] write_file 和 read_file")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        test_file = f.name

    try:
        # 写入
        result = tools.execute("write_file", {"path": test_file, "content": "Hello QingCode!\n测试内容"})
        print(f"  写入结果: {result.success}, {result.output}")

        # 读取
        result = tools.execute("read_file", {"path": test_file})
        print(f"  读取结果: {result.success}, 内容: {result.output}")

        # 编辑
        result = tools.execute("edit_file", {
            "path": test_file,
            "old_content": "Hello",
            "new_content": "Hi"
        })
        print(f"  编辑结果: {result.success}, {result.output}")

        # 再次读取
        result = tools.execute("read_file", {"path": test_file})
        print(f"  编辑后内容: {result.output}")
    finally:
        os.unlink(test_file)

    # 测试Shell命令
    print("\n[测试] run_command")
    result = tools.execute("run_command", {"command": "echo 'Hello from QingCode'"})
    print(f"  结果: {result.success}, 输出: {result.output.strip()}")

    # 测试阻止危险命令
    print("\n[测试] 安全检查 - 阻止危险命令")
    result = tools.execute("run_command", {"command": "rm -rf /"})
    print(f"  结果: {result.success}, 错误: {result.error}")

    # 测试搜索内容
    print("\n[测试] search_content")
    result = tools.execute("search_content", {
        "pattern": "def ",
        "path": ".",
        "file_pattern": "*.py"
    })
    print(f"  结果: {result.success}")
    print(f"  输出预览: {result.output[:150]}...")

    print("\n[OK] 工具系统测试完成")


def test_llm_interface():
    """测试LLM接口"""
    print("\n" + "=" * 50)
    print("测试LLM接口")
    print("=" * 50)

    # 测试配置
    config = LLMConfig(
        provider="openai",
        model="deepseek-chat",
        api_key="test-key",
        base_url="https://api.deepseek.com/v1"
    )

    print(f"\n[测试] LLM配置")
    print(f"  提供商: {config.provider}")
    print(f"  模型: {config.model}")
    print(f"  API地址: {config.base_url}")

    # 测试工具格式转换
    tools = ToolSystem()
    openai_tools = tools.get_openai_tools()

    print(f"\n[测试] 工具格式转换")
    print(f"  工具数量: {len(openai_tools)}")
    print(f"  第一个工具: {openai_tools[0]['function']['name']}")

    print("\n[OK] LLM接口测试完成")


def test_config():
    """测试配置系统"""
    print("\n" + "=" * 50)
    print("测试配置系统")
    print("=" * 50)

    from config import PRESET_CONFIGS

    print("\n[测试] 预设配置")
    for name, config in PRESET_CONFIGS.items():
        print(f"  {name}: {config.model} ({config.provider})")

    print("\n[测试] 默认配置")
    config = QingCodeConfig()
    print(f"  LLM: {config.llm.model}")
    print(f"  Agent最大迭代: {config.agent.max_iterations}")
    print(f"  工具最大文件: {config.tools.max_file_size_mb}MB")

    print("\n[OK] 配置系统测试完成")


def test_agent():
    """测试Agent（需要API Key）"""
    print("\n" + "=" * 50)
    print("测试Agent")
    print("=" * 50)

    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("\n[跳过] 未设置API Key，跳过Agent测试")
        print("  设置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY 后可测试完整功能")
        return

    from agent import Agent

    config = QingCodeConfig()
    config.llm.api_key = api_key
    config.llm.model = "deepseek-chat"
    config.llm.base_url = "https://api.deepseek.com/v1"

    print(f"\n[测试] Agent初始化")
    agent = Agent(config)
    print(f"  [OK] Agent创建成功")

    # 简单测试
    print(f"\n[测试] 简单对话")
    def callback(event_type, data):
        if event_type == "thinking":
            print(f"  {data}")
        elif event_type == "tool_start":
            print(f"  🔧 调用工具: {data['tool']}")

    response = agent.chat("你好，我是QingCode的测试用户", callback=callback)
    print(f"\n  响应: {response[:200]}...")

    print("\n[OK] Agent测试完成")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║                 QingCode 测试套件                            ║
╚══════════════════════════════════════════════════════════════╝
    """)

    try:
        test_config()
        test_tool_system()
        test_llm_interface()
        test_agent()

        print("\n" + "=" * 50)
        print("所有测试完成！")
        print("=" * 50)

    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
