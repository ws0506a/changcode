"""
终端交互界面
"""

import os
import sys
import json
from typing import Optional, List
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table

from agent import Agent
from config import QingCodeConfig, load_config, PRESET_CONFIGS


class Terminal:
    """终端界面"""

    def __init__(self, config: QingCodeConfig):
        self.config = config
        self.agent = Agent(config)
        self.console = Console()
        self.history_file = Path.home() / ".qingcode" / "history.json"

    def run(self):
        """运行主循环"""
        self._show_welcome()

        while True:
            try:
                # 获取用户输入
                user_input = self._get_input()

                if not user_input:
                    continue

                # 处理命令
                if user_input.startswith("/"):
                    if self._handle_command(user_input):
                        continue
                    else:
                        break  # 退出

                # 处理消息
                self._process_message(user_input)

            except KeyboardInterrupt:
                self.console.print("\n[yellow]使用 /exit 退出[/yellow]")
                continue
            except EOFError:
                break

        self.console.print("[green]再见！[/green]")

    def _show_welcome(self):
        """显示欢迎信息"""
        welcome = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ██████╗ ██╗███╗   ██╗ ██████╗  ██████╗ ██████╗ ██████╗ ███████╗  ║
║  ██╔═══██╗██║████╗  ██║██╔════╝ ██╔════╝██╔═══██╗██╔══██╗██╔════╝  ║
║  ██║   ██║██║██╔██╗ ██║██║  ███╗██║     ██║   ██║██║  ██║█████╗    ║
║  ██║▄▄ ██║██║██║╚██╗██║██║   ██║██║     ██║   ██║██║  ██║██╔══╝    ║
║  ╚██████╔╝██║██║ ╚████║╚██████╔╝╚██████╗╚██████╔╝██████╔╝███████╗  ║
║   ╚══▀▀═╝ ╚═╝╚═╝  ╚═══╝ ╚═════╝  ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝  ║
║                                                              ║
║            AI 编程助手 - 由开源大模型驱动                      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
        self.console.print(welcome, style="cyan")
        self.console.print(f"[dim]模型: {self.config.llm.model}[/dim]")
        self.console.print(f"[dim]工作目录: {os.getcwd()}[/dim]")
        self.console.print()
        self.console.print("[green]输入 /help 查看命令，直接输入问题开始对话[/green]")
        self.console.print()

    def _get_input(self) -> str:
        """获取用户输入"""
        try:
            return Prompt.ask("[bold blue]>>>[/bold blue]")
        except:
            return ""

    def _handle_command(self, command: str) -> bool:
        """处理命令，返回 True 继续，False 退出"""
        cmd = command.strip().lower().split()
        if not cmd:
            return True

        cmd_name = cmd[0]

        if cmd_name == "/exit" or cmd_name == "/quit":
            return False

        elif cmd_name == "/help":
            self._show_help()

        elif cmd_name == "/clear":
            os.system('cls' if os.name == 'nt' else 'clear')
            self.agent.reset()
            self.console.print("[green]对话已清空[/green]")

        elif cmd_name == "/reset":
            self.agent.reset()
            self.console.print("[green]Agent 已重置[/green]")

        elif cmd_name == "/history":
            self._show_history()

        elif cmd_name == "/model":
            if len(cmd) > 1:
                self._switch_model(cmd[1])
            else:
                self.console.print(f"当前模型: {self.config.llm.model}")
                self.console.print("可用预设: " + ", ".join(PRESET_CONFIGS.keys()))

        elif cmd_name == "/config":
            self._show_config()

        elif cmd_name == "/save":
            self._save_history()

        elif cmd_name == "/load":
            if len(cmd) > 1:
                self._load_history(cmd[1])
            else:
                self.console.print("[red]请指定文件路径[/red]")

        else:
            self.console.print(f"[red]未知命令: {cmd_name}[/red]")
            self.console.print("输入 /help 查看可用命令")

        return True

    def _show_help(self):
        """显示帮助"""
        help_text = """
[bold cyan]QingCode 命令[/bold cyan]

[bold]基本命令[/bold]
  /help          显示此帮助
  /exit, /quit   退出程序
  /clear         清空对话并重置

[bold]对话管理[/bold]
  /history       显示对话历史
  /reset         重置 Agent
  /save          保存对话到文件
  /load <file>   加载对话文件

[bold]配置[/bold]
  /model [name]  查看/切换模型
  /config        显示当前配置

[bold]使用技巧[/bold]
  - 直接输入问题开始对话
  - Agent 会自动读取和修改文件
  - 修改文件前会请求确认
  - 使用 Ctrl+C 中断当前操作
"""
        self.console.print(Panel(help_text, title="帮助", border_style="cyan"))

    def _show_history(self):
        """显示对话历史"""
        messages = self.agent.get_history()
        
        table = Table(title="对话历史")
        table.add_column("角色", style="cyan")
        table.add_column("内容", style="white")

        for msg in messages:
            role = msg["role"]
            content = msg.get("content", "")
            
            if role == "system":
                continue
            
            if role == "tool":
                content = f"[dim]{content[:100]}...[/dim]"
            elif len(content) > 200:
                content = content[:200] + "..."
            
            table.add_row(role, content or "[工具调用]")

        self.console.print(table)

    def _switch_model(self, model_name: str):
        """切换模型"""
        if model_name in PRESET_CONFIGS:
            self.config.llm = PRESET_CONFIGS[model_name]
            self.agent = Agent(self.config)
            self.console.print(f"[green]已切换到模型: {model_name}[/green]")
        else:
            self.console.print(f"[red]未知模型预设: {model_name}[/red]")
            self.console.print("可用预设: " + ", ".join(PRESET_CONFIGS.keys()))

    def _show_config(self):
        """显示配置"""
        config_info = f"""
[bold cyan]当前配置[/bold cyan]

[bold]LLM 配置[/bold]
  提供商: {self.config.llm.provider}
  模型: {self.config.llm.model}
  API地址: {self.config.llm.base_url or '默认'}
  温度: {self.config.llm.temperature}
  最大Token: {self.config.llm.max_tokens}

[bold]Agent 配置[/bold]
  最大迭代: {self.config.agent.max_iterations}
  自动确认: {self.config.agent.auto_confirm}
  详细模式: {self.config.agent.verbose}

[bold]工具配置[/bold]
  最大文件大小: {self.config.tools.max_file_size_mb}MB
  阻止的命令: {', '.join(self.config.tools.blocked_commands[:3])}...
"""
        self.console.print(Panel(config_info, title="配置", border_style="cyan"))

    def _process_message(self, message: str):
        """处理用户消息"""
        def callback(event_type, data):
            if event_type == "thinking":
                self.console.print(f"[dim]{data}[/dim]")
            elif event_type == "tool_start":
                tool = data["tool"]
                args = data["args"]
                self.console.print(f"[yellow]🔧 调用工具: {tool}[/yellow]")
                if self.config.agent.verbose:
                    self.console.print(f"[dim]参数: {json.dumps(args, ensure_ascii=False)}[/dim]")
            elif event_type == "tool_end":
                tool = data["tool"]
                success = data["success"]
                output = data["output"]
                if success:
                    self.console.print(f"[green]✓ {tool} 完成[/green]")
                    if output and self.config.agent.verbose:
                        self.console.print(f"[dim]{output}[/dim]")
                else:
                    self.console.print(f"[red]✗ {tool} 失败: {output}[/red]")
            elif event_type == "confirm":
                tool = data["tool"]
                args = data["args"]
                self.console.print(f"\n[yellow]⚠️ 需要确认: {tool}[/yellow]")
                self.console.print(f"[dim]参数: {json.dumps(args, ensure_ascii=False)}[/dim]")
                return Confirm.ask("是否继续？")

        # 显示思考状态
        with self.console.status("[bold green]思考中...[/bold green]") as status:
            response = self.agent.chat(message, callback=callback)

        # 显示响应
        self.console.print()
        self.console.print(Panel(Markdown(response), border_style="green"))
        self.console.print()

    def _save_history(self):
        """保存对话历史"""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        history = {
            "config": {
                "model": self.config.llm.model,
                "provider": self.config.llm.provider
            },
            "messages": self.agent.get_history()
        }

        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        self.console.print(f"[green]对话已保存到: {self.history_file}[/green]")

    def _load_history(self, filepath: str):
        """加载对话历史"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                history = json.load(f)

            self.agent.load_history(history["messages"])
            self.console.print(f"[green]已加载对话: {filepath}[/green]")
        except Exception as e:
            self.console.print(f"[red]加载失败: {e}[/red]")
