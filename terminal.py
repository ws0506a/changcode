"""
终端交互界面 - 精美设计版
"""

import os
import sys
import json
import time
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime

from rich.console import Console
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

from agent import Agent
from config import ChangCodeConfig, load_config, PRESET_CONFIGS


# 颜色主题
class Theme:
    PRIMARY = "bright_cyan"
    SECONDARY = "bright_blue"
    ACCENT = "bright_magenta"
    SUCCESS = "bright_green"
    WARNING = "bright_yellow"
    ERROR = "bright_red"
    MUTED = "dim white"
    HIGHLIGHT = "bold bright_white"


class Terminal:
    """终端界面"""

    def __init__(self, config: ChangCodeConfig):
        self.config = config
        self.agent = Agent(config)
        self.console = Console(highlight=True)
        self.history_file = Path.home() / ".changcode" / "history.json"
        self.message_count = 0

    def run(self):
        """运行主循环"""
        self._show_welcome()

        while True:
            try:
                user_input = self._get_input()

                if not user_input:
                    continue

                if user_input.startswith("/"):
                    if self._handle_command(user_input):
                        continue
                    else:
                        break

                self.message_count += 1
                self._process_message(user_input)

            except KeyboardInterrupt:
                self.console.print()
                self.console.print(f"[{Theme.WARNING}]提示: 输入 /exit 退出程序[/{Theme.WARNING}]")
                continue
            except EOFError:
                break

        self._show_goodbye()

    def _show_welcome(self):
        """显示欢迎界面"""
        os.system('cls' if os.name == 'nt' else 'clear')

        logo = """
   ██████╗██╗  ██╗ █████╗ ███╗   ██╗ ██████╗ 
  ██╔════╝██║  ██║██╔══██╗████╗  ██║██╔════╝ 
  ██║     ███████║███████║██╔██╗ ██║██║  ███╗
  ██║     ██╔══██║██╔══██║██║╚██╗██║██║   ██║
  ╚██████╗██║  ██║██║  ██║██║ ╚████║╚██████╔╝
   ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ 
                                              
  ██████╗ ██████╗ ██████╗ ███████╗            
  ██╔════╝██╔═══██╗██╔══██╗██╔════╝            
  ██║     ██║   ██║██║  ██║█████╗              
  ██║     ██║   ██║██║  ██║██╔══╝              
  ╚██████╗╚██████╔╝██████╔╝███████╗            
   ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝            
        """

        self.console.print(logo, style=Theme.PRIMARY)
        
        # 信息卡片
        info_cards = [
            Panel(
                Align.center(f"[{Theme.HIGHLIGHT}]{self.config.llm.model}[/{Theme.HIGHLIGHT}]\n[{Theme.MUTED}]模型引擎[/{Theme.MUTED}]"),
                border_style=Theme.PRIMARY,
                padding=(0, 2)
            ),
            Panel(
                Align.center(f"[{Theme.HIGHLIGHT}]v1.0.0[/{Theme.HIGHLIGHT}]\n[{Theme.MUTED}]版本[/{Theme.MUTED}]"),
                border_style=Theme.SECONDARY,
                padding=(0, 2)
            ),
            Panel(
                Align.center(f"[{Theme.HIGHLIGHT}]8[/{Theme.HIGHLIGHT}]\n[{Theme.MUTED}]工具集[/{Theme.MUTED}]"),
                border_style=Theme.ACCENT,
                padding=(0, 2)
            ),
        ]
        
        self.console.print(Columns(info_cards, expand=True, equal=True))
        self.console.print()
        
        # 快速提示
        tips = [
            "[bright_cyan]  直接输入[/bright_cyan] [bright_white]开始对话[/bright_white]",
            "[bright_cyan]  /help[/bright_cyan]        [dim]查看所有命令[/dim]",
            "[bright_cyan]  /model[/bright_cyan]       [dim]切换AI模型[/dim]",
            "[bright_cyan]  Ctrl+C[/bright_cyan]       [dim]中断当前任务[/dim]",
        ]
        
        self.console.print(Panel(
            "\n".join(tips),
            title=f"[{Theme.HIGHLIGHT}] 快速开始 [/{Theme.HIGHLIGHT}]",
            border_style=Theme.MUTED,
            padding=(1, 2)
        ))
        
        self.console.print()

    def _show_goodbye(self):
        """显示告别界面"""
        self.console.print()
        self.console.print(Rule(style=Theme.MUTED))
        
        goodbye_text = Text()
        goodbye_text.append("感谢使用 ", style=Theme.MUTED)
        goodbye_text.append("ChangCode", style=f"bold {Theme.PRIMARY}")
        goodbye_text.append(" !", style=Theme.MUTED)
        
        self.console.print(Align.center(goodbye_text))
        self.console.print(Align.center(f"[{Theme.MUTED}]本次会话共处理 {self.message_count} 条消息[/{Theme.MUTED}]"))
        self.console.print()

    def _get_input(self) -> str:
        """获取用户输入"""
        try:
            # 动态提示符
            prompt_text = Text()
            prompt_text.append("❯ ", style=f"bold {Theme.PRIMARY}")
            
            return Prompt.ask(prompt_text)
        except:
            return ""

    def _handle_command(self, command: str) -> bool:
        """处理命令"""
        cmd = command.strip().lower().split()
        if not cmd:
            return True

        cmd_name = cmd[0]
        commands = {
            "/exit": self._cmd_exit,
            "/quit": self._cmd_exit,
            "/help": self._cmd_help,
            "/clear": self._cmd_clear,
            "/reset": self._cmd_reset,
            "/history": self._cmd_history,
            "/model": lambda: self._cmd_model(cmd[1:] if len(cmd) > 1 else []),
            "/config": self._cmd_config,
            "/save": self._cmd_save,
            "/load": lambda: self._cmd_load(cmd[1] if len(cmd) > 1 else None),
            "/about": self._cmd_about,
        }

        if cmd_name in commands:
            result = commands[cmd_name]()
            return result if isinstance(result, bool) else True
        else:
            self.console.print(Panel(
                f"[{Theme.ERROR}]未知命令: {cmd_name}[/{Theme.ERROR}]\n\n[{Theme.MUTED}]输入 /help 查看可用命令[/{Theme.MUTED}]",
                border_style=Theme.ERROR,
                padding=(0, 1)
            ))
            return True

    def _cmd_exit(self) -> bool:
        return False

    def _cmd_help(self):
        """显示帮助"""
        self.console.print()
        
        # 基本命令
        basic_cmds = [
            ("/help", "显示帮助信息"),
            ("/exit", "退出程序"),
            ("/clear", "清空对话历史"),
            ("/reset", "重置Agent状态"),
        ]
        
        # 对话管理
        chat_cmds = [
            ("/history", "查看对话历史"),
            ("/save", "保存当前对话"),
            ("/load <file>", "加载历史对话"),
        ]
        
        # 配置
        config_cmds = [
            ("/model [name]", "查看/切换模型"),
            ("/config", "显示当前配置"),
            ("/about", "关于ChangCode"),
        ]

        def render_cmd_table(title: str, cmds: list, icon: str) -> Table:
            table = Table(
                title=f" {icon} {title} ",
                box=box.SIMPLE_HEAVY,
                border_style=Theme.MUTED,
                title_style=f"bold {Theme.PRIMARY}",
                show_header=False,
                padding=(0, 2)
            )
            table.add_column("命令", style=Theme.HIGHLIGHT, min_width=20)
            table.add_column("说明", style=Theme.MUTED)
            
            for cmd, desc in cmds:
                table.add_row(cmd, desc)
            
            return table

        self.console.print(render_cmd_table("基本命令", basic_cmds, "◆"))
        self.console.print()
        self.console.print(render_cmd_table("对话管理", chat_cmds, "◆"))
        self.console.print()
        self.console.print(render_cmd_table("系统配置", config_cmds, "◆"))
        
        # 使用技巧
        tips_panel = Panel(
            "\n".join([
                f"[{Theme.ACCENT}]•[/{Theme.ACCENT}] 直接输入文字开始与AI对话",
                f"[{Theme.ACCENT}]•[/{Theme.ACCENT}] AI可以读写文件、执行命令、搜索代码",
                f"[{Theme.ACCENT}]•[/{Theme.ACCENT}] 敏感操作前会请求确认",
                f"[{Theme.ACCENT}]•[/{Theme.ACCENT}] 使用 -v 参数启用详细模式查看更多信息",
            ]),
            title=f"[{Theme.HIGHLIGHT}] 使用技巧 [/{Theme.HIGHLIGHT}]",
            border_style=Theme.SECONDARY,
            padding=(1, 2)
        )
        
        self.console.print()
        self.console.print(tips_panel)
        self.console.print()

    def _cmd_clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.agent.reset()
        self._show_welcome()
        self.console.print(f"[{Theme.SUCCESS}]✓ 对话已清空[/{Theme.SUCCESS}]")
        self.console.print()

    def _cmd_reset(self):
        self.agent.reset()
        self.console.print(Panel(
            f"[{Theme.SUCCESS}]Agent 已重置[/{Theme.SUCCESS}]",
            border_style=Theme.SUCCESS,
            padding=(0, 1)
        ))

    def _cmd_history(self):
        messages = self.agent.get_history()

        if len(messages) <= 1:
            self.console.print(Panel(
                f"[{Theme.MUTED}]暂无对话历史[/{Theme.MUTED}]",
                border_style=Theme.MUTED,
                padding=(0, 1)
            ))
            return

        table = Table(
            title=f" 对话历史 (共 {len(messages)-1} 条) ",
            box=box.ROUNDED,
            border_style=Theme.PRIMARY,
            title_style=f"bold {Theme.PRIMARY}",
            show_lines=True
        )
        table.add_column("#", style=Theme.MUTED, width=4, justify="right")
        table.add_column("角色", style=Theme.HIGHLIGHT, width=10)
        table.add_column("内容", style="white")

        idx = 0
        for msg in messages:
            role = msg["role"]
            content = msg.get("content", "")

            if role == "system":
                continue

            idx += 1

            role_display = {
                "user": f"[{Theme.PRIMARY}]用户[/{Theme.PRIMARY}]",
                "assistant": f"[{Theme.ACCENT}]AI[/{Theme.ACCENT}]",
                "tool": f"[{Theme.WARNING}]工具[/{Theme.WARNING}]",
            }.get(role, role)

            if role == "tool":
                content = f"[{Theme.MUTED}]{content[:80]}...[/{Theme.MUTED}]"
            elif len(content) > 150:
                content = content[:150] + f"[{Theme.MUTED}]...[/{Theme.MUTED}]"

            table.add_row(str(idx), role_display, content or f"[{Theme.MUTED}][工具调用][/{Theme.MUTED}]")

        self.console.print()
        self.console.print(table)
        self.console.print()

    def _cmd_model(self, args: list):
        if args:
            model_name = args[0]
            if model_name in PRESET_CONFIGS:
                self.config.llm = PRESET_CONFIGS[model_name]
                self.agent = Agent(self.config)
                self.console.print(Panel(
                    f"[{Theme.SUCCESS}]✓ 已切换到模型: {model_name}[/{Theme.SUCCESS}]",
                    border_style=Theme.SUCCESS,
                    padding=(0, 1)
                ))
            else:
                self.console.print(Panel(
                    f"[{Theme.ERROR}]✗ 未知模型: {model_name}[/{Theme.ERROR}]",
                    border_style=Theme.ERROR,
                    padding=(0, 1)
                ))
        else:
            # 显示当前模型和可用模型
            self.console.print()
            
            current_model = Panel(
                Align.center(
                    f"[{Theme.HIGHLIGHT}]{self.config.llm.model}[/{Theme.HIGHLIGHT}]\n"
                    f"[{Theme.MUTED}]{self.config.llm.provider}[/{Theme.MUTED}]"
                ),
                title=f" 当前模型 ",
                border_style=Theme.PRIMARY,
                padding=(1, 3)
            )
            
            self.console.print(current_model)
            self.console.print()
            
            # 可用模型列表
            model_table = Table(
                title=" 可用模型 ",
                box=box.SIMPLE,
                border_style=Theme.MUTED,
                show_header=True,
                header_style=f"bold {Theme.SECONDARY}"
            )
            model_table.add_column("名称", style=Theme.HIGHLIGHT, min_width=15)
            model_table.add_column("模型", style="white", min_width=25)
            model_table.add_column("提供商", style=Theme.MUTED, min_width=10)

            for name, cfg in PRESET_CONFIGS.items():
                is_current = "▸ " if name == self.config.llm.provider else "  "
                model_table.add_row(
                    f"{is_current}{name}",
                    cfg.model,
                    cfg.provider
                )

            self.console.print(model_table)
            self.console.print(f"\n[{Theme.MUTED}]使用 /model <名称> 切换模型[/{Theme.MUTED}]")
            self.console.print()

    def _cmd_config(self):
        config_content = f"""[bold {Theme.PRIMARY}]模型配置[/bold {Theme.PRIMARY}]
  [{Theme.HIGHLIGHT}]提供商:[/{Theme.HIGHLIGHT}] {self.config.llm.provider}
  [{Theme.HIGHLIGHT}]模型:[/{Theme.HIGHLIGHT}] {self.config.llm.model}
  [{Theme.HIGHLIGHT}]API地址:[/{Theme.HIGHLIGHT}] {self.config.llm.base_url or '默认'}
  [{Theme.HIGHLIGHT}]温度:[/{Theme.HIGHLIGHT}] {self.config.llm.temperature}
  [{Theme.HIGHLIGHT}]最大Token:[/{Theme.HIGHLIGHT}] {self.config.llm.max_tokens}

[bold {Theme.PRIMARY}]Agent配置[/bold {Theme.PRIMARY}]
  [{Theme.HIGHLIGHT}]最大迭代:[/{Theme.HIGHLIGHT}] {self.config.agent.max_iterations}
  [{Theme.HIGHLIGHT}]自动确认:[/{Theme.HIGHLIGHT}] {'启用' if self.config.agent.auto_confirm else '禁用'}
  [{Theme.HIGHLIGHT}]详细模式:[/{Theme.HIGHLIGHT}] {'启用' if self.config.agent.verbose else '禁用'}

[bold {Theme.PRIMARY}]工具配置[/bold {Theme.PRIMARY}]
  [{Theme.HIGHLIGHT}]文件大小限制:[/{Theme.HIGHLIGHT}] {self.config.tools.max_file_size_mb}MB
  [{Theme.HIGHLIGHT}]安全命令:[/{Theme.HIGHLIGHT}] {len(self.config.tools.blocked_commands)}个已阻止"""

        self.console.print()
        self.console.print(Panel(
            config_content,
            title=f" 系统配置 ",
            border_style=Theme.PRIMARY,
            padding=(1, 2)
        ))
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

        self.console.print(Panel(
            f"[{Theme.SUCCESS}]✓ 对话已保存[/{Theme.SUCCESS}]\n\n[{Theme.MUTED}]文件: {self.history_file}[/{Theme.MUTED}]",
            border_style=Theme.SUCCESS,
            padding=(1, 2)
        ))

    def _cmd_load(self, filepath: Optional[str]):
        if not filepath:
            self.console.print(Panel(
                f"[{Theme.ERROR}]请指定文件路径[/{Theme.ERROR}]\n\n[{Theme.MUTED}]用法: /load <文件路径>[/{Theme.MUTED}]",
                border_style=Theme.ERROR,
                padding=(1, 2)
            ))
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                history = json.load(f)

            self.agent.load_history(history["messages"])
            self.console.print(Panel(
                f"[{Theme.SUCCESS}]✓ 对话已加载[/{Theme.SUCCESS}]\n\n[{Theme.MUTED}]来自: {filepath}[/{Theme.MUTED}]",
                border_style=Theme.SUCCESS,
                padding=(1, 2)
            ))
        except Exception as e:
            self.console.print(Panel(
                f"[{Theme.ERROR}]✗ 加载失败[/{Theme.ERROR}]\n\n[{Theme.MUTED}]{e}[/{Theme.MUTED}]",
                border_style=Theme.ERROR,
                padding=(1, 2)
            ))

    def _cmd_about(self):
        about_text = f"""
[{Theme.HIGHLIGHT}]ChangCode[/{Theme.HIGHLIGHT}] [{Theme.MUTED}]v1.0.0[/{Theme.MUTED}]

由开源大模型驱动的AI编程助手
类似 Claude Code，但使用国产模型

[{Theme.PRIMARY}]特性:[/{Theme.PRIMARY}]
  • 支持 DeepSeek / GLM / Qwen / GPT / Claude
  • 文件读写、代码搜索、命令执行
  • 智能Agent循环（规划→执行→验证）
  • 安全的权限控制

[{Theme.PRIMARY}]技术栈:[/{Theme.PRIMARY}]
  Python + Rich + OpenAI API

[{Theme.PRIMARY}]项目:[/{Theme.PRIMARY}]
  https://github.com/ws0506a/changcode
"""
        self.console.print()
        self.console.print(Panel(
            about_text,
            title=f" 关于 ChangCode ",
            border_style=Theme.ACCENT,
            padding=(1, 2)
        ))
        self.console.print()

    def _process_message(self, message: str):
        """处理用户消息"""
        self.console.print()
        
        def callback(event_type, data):
            if event_type == "thinking":
                self.console.print(f"[{Theme.MUTED}]  {data}[/{Theme.MUTED}]")
            elif event_type == "tool_start":
                tool = data["tool"]
                tool_icons = {
                    "read_file": "📖",
                    "write_file": "📝",
                    "edit_file": "✏️",
                    "run_command": "⚡",
                    "search_files": "🔍",
                    "search_content": "🔎",
                    "list_directory": "📁",
                    "get_current_dir": "📍",
                }
                icon = tool_icons.get(tool, "🔧")
                self.console.print(f"  [{Theme.WARNING}]{icon} {tool}[/{Theme.WARNING}]")
                if self.config.agent.verbose:
                    args_str = json.dumps(data["args"], ensure_ascii=False)
                    self.console.print(f"  [{Theme.MUTED}]  {args_str}[/{Theme.MUTED}]")
            elif event_type == "tool_end":
                tool = data["tool"]
                success = data["success"]
                if success:
                    self.console.print(f"  [{Theme.SUCCESS}]  ✓ 完成[/{Theme.SUCCESS}]")
                    if self.config.agent.verbose and data["output"]:
                        output = data["output"][:200]
                        self.console.print(f"  [{Theme.MUTED}]  {output}[/{Theme.MUTED}]")
                else:
                    self.console.print(f"  [{Theme.ERROR}]  ✗ 失败: {data['output']}[/{Theme.ERROR}]")
            elif event_type == "confirm":
                tool = data["tool"]
                self.console.print()
                self.console.print(Panel(
                    f"[{Theme.WARNING}]⚠️  即将执行: {tool}[/{Theme.WARNING}]",
                    border_style=Theme.WARNING,
                    padding=(0, 1)
                ))
                return Confirm.ask(f"[{Theme.HIGHLIGHT}]是否继续？[/{Theme.HIGHLIGHT}]")

        with self.console.status(f"[bold {Theme.PRIMARY}]思考中...[/bold {Theme.PRIMARY}]") as status:
            response = self.agent.chat(message, callback=callback)

        self.console.print()
        self.console.print(Rule(style=Theme.MUTED))
        self.console.print()
        self.console.print(Panel(
            Markdown(response),
            title=f" [{Theme.ACCENT}]ChangCode[/{Theme.ACCENT}] ",
            border_style=Theme.ACCENT,
            padding=(1, 2)
        ))
        self.console.print()
