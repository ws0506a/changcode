"""
ChangCode Terminal - Claude Code风格界面
"""

import os
import sys
import json
import time
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime

from rich.console import Console, Group
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
from rich.align import Align
from rich.text import Text
from rich.rule import Rule
from rich.columns import Columns
from rich import box
from rich.layout import Layout
from rich.console import RenderableType

from agent import Agent
from config import ChangCodeConfig, load_config, PRESET_CONFIGS


class Theme:
    """Claude Code风格配色"""
    PRIMARY = "#00d4aa"
    SECONDARY = "#6c5ce7"
    ACCENT = "#fd79a8"
    SUCCESS = "#00b894"
    WARNING = "#fdcb6e"
    ERROR = "#ff7675"
    MUTED = "#636e72"
    TEXT = "#dfe6e9"
    USER_BG = "#0984e3"
    AI_BG = "#00b894"


class Terminal:
    """终端界面 - Claude Code风格"""

    def __init__(self, config: ChangCodeConfig):
        self.config = config
        self.agent = Agent(config)
        self.console = Console(highlight=True)
        self.history_file = Path.home() / ".changcode" / "history.json"
        self.message_count = 0
        self.session_start = datetime.now()

    def run(self):
        """运行主循环"""
        self._show_welcome()

        while True:
            try:
                self._show_status_bar()
                user_input = self._get_input()

                if not user_input:
                    continue

                if user_input.startswith("/"):
                    if self._handle_command(user_input):
                        continue
                    else:
                        break

                if user_input.lower() in ["exit", "quit", "q"]:
                    break

                self.message_count += 1
                self._process_message(user_input)

            except KeyboardInterrupt:
                self.console.print()
                self.console.print(f"[dim]提示: 输入 /exit 或 exit 退出[/dim]")
                continue
            except EOFError:
                break

        self._show_goodbye()

    def _show_welcome(self):
        """显示欢迎界面 - Claude Code风格"""
        os.system('cls' if os.name == 'nt' else 'clear')

        logo = """
 ╔═══════════════════════════════════════════════════════════════╗
 ║                                                               ║
 ║    ██████╗██╗  ██╗ █████╗ ███╗   ██╗ ██████╗ ██████╗ ██████╗  ║
 ║   ██╔════╝██║  ██║██╔══██╗████╗  ██║██╔════╝██╔════╝██╔═══██╗ ║
 ║   ██║     ███████║███████║██╔██╗ ██║██║     ██║     ██║   ██║ ║
 ║   ██║     ██╔══██║██╔══██║██║╚██╗██║██║     ██║     ██║   ██║ ║
 ║   ╚██████╗██║  ██║██║  ██║██║ ╚████║╚██████╗╚██████╗╚██████╔╝ ║
 ║    ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═════╝ ╚═════╝  ║
 ║                                                               ║
 ║           AI Coding Assistant · Powered by Open Source LLM    ║
 ║                                                               ║
 ╚═══════════════════════════════════════════════════════════════╝
        """

        self.console.print(logo, style=f"bold {Theme.PRIMARY}")
        
        # 信息行
        info_line = Text()
        info_line.append("  Model: ", style=Theme.MUTED)
        info_line.append(f"{self.config.llm.model}", style=f"bold {Theme.TEXT}")
        info_line.append("  │  ", style=Theme.MUTED)
        info_line.append("Version: ", style=Theme.MUTED)
        info_line.append("1.0.0", style=f"bold {Theme.TEXT}")
        info_line.append("  │  ", style=Theme.MUTED)
        info_line.append("Tools: ", style=Theme.MUTED)
        info_line.append("8", style=f"bold {Theme.TEXT}")
        
        self.console.print(info_line)
        self.console.print()
        
        # 快速命令提示
        self.console.print(Panel(
            "[bold]Quick Start[/bold]\n\n"
            f"  [{Theme.PRIMARY}]直接输入[/{Theme.PRIMARY}]  开始对话\n"
            f"  [{Theme.PRIMARY}]/help[/{Theme.PRIMARY}]        查看所有命令\n"
            f"  [{Theme.PRIMARY}]/model[/{Theme.PRIMARY}]       切换AI模型\n"
            f"  [{Theme.PRIMARY}]Ctrl+C[/{Theme.PRIMARY}]       中断当前任务",
            border_style=Theme.MUTED,
            padding=(1, 2),
            title="[dim]帮助[/dim]",
            title_align="left"
        ))
        self.console.print()

    def _show_status_bar(self):
        """显示状态栏 - Claude Code风格"""
        status = Text()
        
        # 模型信息
        status.append(f" {self.config.llm.model} ", style=f"black on {Theme.PRIMARY}")
        status.append(" ", style="default")
        
        # 目录信息
        cwd = os.getcwd()
        if len(cwd) > 30:
            cwd = "..." + cwd[-27:]
        status.append(f" {cwd} ", style=f"black on {Theme.SECONDARY}")
        status.append(" ", style="default")
        
        # 会话信息
        status.append(f" msg:{self.message_count} ", style=f"black on {Theme.ACCENT}")
        
        self.console.print(status)
        self.console.print()

    def _get_input(self) -> str:
        """获取用户输入"""
        try:
            prompt = Text()
            prompt.append(" ❯ ", style=f"bold {Theme.PRIMARY}")
            return Prompt.ask(prompt)
        except:
            return ""

    def _handle_command(self, command: str) -> bool:
        """处理命令"""
        cmd = command.strip().lower().split()
        if not cmd:
            return True

        cmd_name = cmd[0]
        
        commands = {
            "/exit": lambda: False,
            "/quit": lambda: False,
            "/help": self._cmd_help,
            "/clear": self._cmd_clear,
            "/reset": self._cmd_reset,
            "/history": self._cmd_history,
            "/model": lambda: self._cmd_model(cmd[1:] if len(cmd) > 1 else []),
            "/config": self._cmd_config,
            "/save": self._cmd_save,
            "/load": lambda: self._cmd_load(cmd[1] if len(cmd) > 1 else None),
            "/about": self._cmd_about,
            "/shortcuts": self._cmd_shortcuts,
        }

        if cmd_name in commands:
            result = commands[cmd_name]()
            return result if isinstance(result, bool) else True
        else:
            self.console.print(f"[{Theme.ERROR}]Unknown command: {cmd_name}[/{Theme.ERROR}]")
            self.console.print(f"[dim]Type /help for available commands[/dim]")
            return True

    def _cmd_help(self):
        """显示帮助 - Claude Code风格"""
        self.console.print()
        
        # 基本命令
        basic = Table(
            box=box.SIMPLE_HEAVY,
            show_header=False,
            padding=(0, 2),
            border_style=Theme.MUTED
        )
        basic.add_column("Command", style=f"bold {Theme.PRIMARY}", min_width=16)
        basic.add_column("Description", style=Theme.TEXT)
        
        basic.add_row("/help", "Show this help message")
        basic.add_row("/exit, exit", "Exit the program")
        basic.add_row("/clear", "Clear conversation history")
        basic.add_row("/reset", "Reset agent state")
        basic.add_row("/shortcuts", "Show keyboard shortcuts")
        
        # 对话管理
        chat = Table(
            box=box.SIMPLE_HEAVY,
            show_header=False,
            padding=(0, 2),
            border_style=Theme.MUTED
        )
        chat.add_column("Command", style=f"bold {Theme.PRIMARY}", min_width=16)
        chat.add_column("Description", style=Theme.TEXT)
        
        chat.add_row("/history", "View conversation history")
        chat.add_row("/save", "Save current conversation")
        chat.add_row("/load <file>", "Load saved conversation")
        
        # 配置
        config = Table(
            box=box.SIMPLE_HEAVY,
            show_header=False,
            padding=(0, 2),
            border_style=Theme.MUTED
        )
        config.add_column("Command", style=f"bold {Theme.PRIMARY}", min_width=16)
        config.add_column("Description", style=Theme.TEXT)
        
        config.add_row("/model [name]", "View/switch AI model")
        config.add_row("/config", "Show current configuration")
        config.add_row("/about", "About ChangCode")
        
        self.console.print(Panel(basic, title=f"[bold {Theme.PRIMARY}]基本命令[/bold {Theme.PRIMARY}]", border_style=Theme.MUTED))
        self.console.print()
        self.console.print(Panel(chat, title=f"[bold {Theme.PRIMARY}]对话管理[/bold {Theme.PRIMARY}]", border_style=Theme.MUTED))
        self.console.print()
        self.console.print(Panel(config, title=f"[bold {Theme.PRIMARY}]系统配置[/bold {Theme.PRIMARY}]", border_style=Theme.MUTED))
        self.console.print()

    def _cmd_shortcuts(self):
        """显示快捷键"""
        shortcuts = Table(
            box=box.SIMPLE_HEAVY,
            show_header=True,
            header_style=f"bold {Theme.PRIMARY}",
            border_style=Theme.MUTED
        )
        shortcuts.add_column("Shortcut", style=f"bold {Theme.PRIMARY}", min_width=20)
        shortcuts.add_column("Action", style=Theme.TEXT)
        
        shortcuts.add_row("Ctrl+C", "Interrupt current task")
        shortcuts.add_row("Ctrl+D / exit", "Exit program")
        shortcuts.add_row("↑ / ↓", "Navigate command history")
        shortcuts.add_row("Tab", "Auto-complete")
        shortcuts.add_row("Ctrl+L", "Clear screen")
        shortcuts.add_row("Ctrl+U", "Clear current line")
        shortcuts.add_row("Ctrl+W", "Delete word before cursor")
        shortcuts.add_row("Ctrl+A", "Move cursor to start")
        shortcuts.add_row("Ctrl+E", "Move cursor to end")
        
        self.console.print()
        self.console.print(Panel(shortcuts, title=f"[bold {Theme.PRIMARY}]Keyboard Shortcuts[/bold {Theme.PRIMARY}]", border_style=Theme.MUTED))
        self.console.print()

    def _cmd_clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.agent.reset()
        self.message_count = 0
        self._show_welcome()
        self.console.print(f"[{Theme.SUCCESS}]✓ Conversation cleared[/{Theme.SUCCESS}]")
        self.console.print()

    def _cmd_reset(self):
        self.agent.reset()
        self.console.print(f"[{Theme.SUCCESS}]✓ Agent reset[/{Theme.SUCCESS}]")

    def _cmd_history(self):
        messages = self.agent.get_history()

        if len(messages) <= 1:
            self.console.print(f"[dim]No conversation history[/dim]")
            return

        self.console.print()
        
        for i, msg in enumerate(messages):
            if msg["role"] == "system":
                continue
                
            role = msg["role"]
            content = msg.get("content", "") or "[tool call]"
            
            # 角色标签
            if role == "user":
                role_display = Text(" You ", style=f"black on {Theme.USER_BG}")
            elif role == "assistant":
                role_display = Text(" ChangCode ", style=f"black on {Theme.AI_BG}")
            elif role == "tool":
                role_display = Text(" Tool ", style=f"black on {Theme.WARNING}")
            else:
                continue
            
            # 内容截断
            if len(content) > 200:
                content = content[:200] + "..."
            
            self.console.print(role_display)
            self.console.print(f"  {content}")
            self.console.print()

    def _cmd_model(self, args: list):
        if args:
            model_name = args[0]
            if model_name in PRESET_CONFIGS:
                self.config.llm = PRESET_CONFIGS[model_name]
                self.agent = Agent(self.config)
                self.console.print(f"[{Theme.SUCCESS}]✓ Switched to model: {model_name}[/{Theme.SUCCESS}]")
            else:
                self.console.print(f"[{Theme.ERROR}]Unknown model: {model_name}[/{Theme.ERROR}]")
        else:
            self.console.print()
            
            # 当前模型
            self.console.print(Panel(
                f"[bold {Theme.TEXT}]{self.config.llm.model}[/bold {Theme.TEXT}]\n"
                f"[dim]{self.config.llm.provider}[/dim]",
                title=f"[bold {Theme.PRIMARY}]Current Model[/bold {Theme.PRIMARY}]",
                border_style=Theme.PRIMARY,
                padding=(1, 3)
            ))
            self.console.print()
            
            # 可用模型
            models = Table(
                box=box.SIMPLE,
                show_header=True,
                header_style=f"bold {Theme.PRIMARY}",
                border_style=Theme.MUTED
            )
            models.add_column("Name", style=f"bold {Theme.TEXT}", min_width=15)
            models.add_column("Model", style=Theme.TEXT, min_width=25)
            models.add_column("Provider", style=Theme.MUTED, min_width=10)

            for name, cfg in PRESET_CONFIGS.items():
                marker = "▸ " if name == self.config.llm.provider else "  "
                models.add_row(f"{marker}{name}", cfg.model, cfg.provider)

            self.console.print(models)
            self.console.print(f"\n[dim]Use /model <name> to switch[/dim]")
            self.console.print()

    def _cmd_config(self):
        config_text = f"""[bold {Theme.PRIMARY}]Model[/bold {Theme.PRIMARY}]
  Provider: {self.config.llm.provider}
  Model: {self.config.llm.model}
  Base URL: {self.config.llm.base_url or 'default'}
  Temperature: {self.config.llm.temperature}
  Max Tokens: {self.config.llm.max_tokens}

[bold {Theme.PRIMARY}]Agent[/bold {Theme.PRIMARY}]
  Max Iterations: {self.config.agent.max_iterations}
  Auto Confirm: {'enabled' if self.config.agent.auto_confirm else 'disabled'}
  Verbose: {'enabled' if self.config.agent.verbose else 'disabled'}

[bold {Theme.PRIMARY}]Tools[/bold {Theme.PRIMARY}]
  File Size Limit: {self.config.tools.max_file_size_mb}MB
  Blocked Commands: {len(self.config.tools.blocked_commands)} rules"""

        self.console.print()
        self.console.print(Panel(config_text, title=f"[bold {Theme.PRIMARY}]Configuration[/bold {Theme.PRIMARY}]", border_style=Theme.MUTED, padding=(1, 2)))
        self.console.print()

    def _cmd_save(self):
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

        history = {
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "config": {
                "model": self.config.llm.model,
                "provider": self.config.llm.provider
            },
            "messages": self.agent.get_history()
        }

        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        self.console.print(f"[{Theme.SUCCESS}]✓ Conversation saved to {self.history_file}[/{Theme.SUCCESS}]")

    def _cmd_load(self, filepath: Optional[str]):
        if not filepath:
            self.console.print(f"[{Theme.ERROR}]Please specify file path[/{Theme.ERROR}]")
            self.console.print(f"[dim]Usage: /load <file_path>[/dim]")
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                history = json.load(f)

            self.agent.load_history(history["messages"])
            self.console.print(f"[{Theme.SUCCESS}]✓ Conversation loaded from {filepath}[/{Theme.SUCCESS}]")
        except Exception as e:
            self.console.print(f"[{Theme.ERROR}]Load failed: {e}[/{Theme.ERROR}]")

    def _cmd_about(self):
        about = f"""
[{Theme.PRIMARY}]ChangCode[/[{Theme.PRIMARY}] [dim]v1.0.0[/dim]

AI coding assistant powered by open source LLM
Like Claude Code, but using domestic models

[{Theme.PRIMARY}]Features:[/{Theme.PRIMARY}]
  • Support DeepSeek / GLM / Qwen / GPT / Claude
  • File read/write, code search, command execution
  • Smart agent loop (plan → execute → verify)
  • Secure permission control

[{Theme.PRIMARY}]Tech Stack:[/{Theme.PRIMARY}]
  Python + Rich + OpenAI API

[{Theme.PRIMARY}]Project:[/{Theme.PRIMARY}]
  https://github.com/ws0506a/changcode
"""
        self.console.print()
        self.console.print(Panel(about, title=f"[bold {Theme.PRIMARY}]About[/bold {Theme.PRIMARY}]", border_style=Theme.MUTED, padding=(1, 2)))
        self.console.print()

    def _process_message(self, message: str):
        """处理用户消息 - Claude Code风格"""
        self.console.print()
        
        # 显示用户消息
        user_panel = Panel(
            message,
            title=f"[bold black on {Theme.USER_BG}] You [/bold black on {Theme.USER_BG}]",
            border_style=Theme.USER_BG,
            padding=(0, 1)
        )
        self.console.print(user_panel)
        self.console.print()
        
        tool_calls = []
        
        def callback(event_type, data):
            if event_type == "thinking":
                self.console.print(f"[dim]  Thinking...[/dim]")
            elif event_type == "tool_start":
                tool = data["tool"]
                tool_calls.append({"tool": tool, "success": False})
            elif event_type == "tool_end":
                tool = data["tool"]
                success = data["success"]
                for tc in tool_calls:
                    if tc["tool"] == tool:
                        tc["success"] = success
            elif event_type == "confirm":
                tool = data["tool"]
                self.console.print()
                self.console.print(Panel(
                    f"[{Theme.WARNING}]⚠️  About to execute: {tool}[/{Theme.WARNING}]",
                    border_style=Theme.WARNING,
                    padding=(0, 1)
                ))
                return Confirm.ask(f"[bold {Theme.TEXT}]Continue?[/bold {Theme.TEXT}]")

        # 执行Agent
        with self.console.status(f"[bold {Theme.PRIMARY}]Processing...[/bold {Theme.PRIMARY}]") as status:
            response = self.agent.chat(message, callback=callback)

        # 显示工具调用
        if tool_calls:
            self.console.print()
            for tc in tool_calls:
                status_icon = "✓" if tc["success"] else "✗"
                status_color = Theme.SUCCESS if tc["success"] else Theme.ERROR
                self.console.print(f"  [{status_color}]{status_icon}[/{status_color}] {tc['tool']}")
        
        # 显示AI响应
        self.console.print()
        ai_panel = Panel(
            Markdown(response),
            title=f"[bold black on {Theme.AI_BG}] ChangCode [/bold black on {Theme.AI_BG}]",
            border_style=Theme.AI_BG,
            padding=(1, 2)
        )
        self.console.print(ai_panel)
        self.console.print()

    def _show_goodbye(self):
        """显示告别界面"""
        duration = (datetime.now() - self.session_start).seconds
        
        goodbye = f"""
 ╔═══════════════════════════════════════════════════════════════╗
 ║                                                               ║
 ║   Thanks for using ChangCode!                                 ║
 ║                                                               ║
 ║   Session: {self.message_count} messages · {duration}s duration                    ║
 ║                                                               ║
 ╚═══════════════════════════════════════════════════════════════╝
        """
        
        self.console.print(goodbye, style=f"bold {Theme.PRIMARY}")
