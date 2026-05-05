"""
工具系统 - 文件操作、Shell命令、代码搜索等
"""

import os
import subprocess
import glob as glob_module
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass

from config import ToolConfig


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    output: str
    error: str = ""

    def __str__(self):
        if self.success:
            return self.output
        return f"Error: {self.error}"


class Tool:
    """工具定义"""
    def __init__(self, name: str, description: str, parameters: Dict, 
                 handler: Callable, requires_confirmation: bool = False):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler
        self.requires_confirmation = requires_confirmation

    def to_openai_format(self) -> Dict:
        """转换为 OpenAI 工具格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

    def execute(self, **kwargs) -> ToolResult:
        """执行工具"""
        try:
            return self.handler(**kwargs)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class ToolSystem:
    """工具系统"""

    def __init__(self, config: ToolConfig = None):
        self.config = config or ToolConfig()
        self.tools: Dict[str, Tool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """注册默认工具"""
        # 文件读取
        self.register(Tool(
            name="read_file",
            description="读取文件内容",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"}
                },
                "required": ["path"]
            },
            handler=self._read_file
        ))

        # 文件写入
        self.register(Tool(
            name="write_file",
            description="写入或创建文件",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                    "content": {"type": "string", "description": "文件内容"}
                },
                "required": ["path", "content"]
            },
            handler=self._write_file,
            requires_confirmation=True
        ))

        # 文件编辑
        self.register(Tool(
            name="edit_file",
            description="编辑文件中的特定内容",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                    "old_content": {"type": "string", "description": "要替换的旧内容"},
                    "new_content": {"type": "string", "description": "新内容"}
                },
                "required": ["path", "old_content", "new_content"]
            },
            handler=self._edit_file,
            requires_confirmation=True
        ))

        # Shell 命令
        self.register(Tool(
            name="run_command",
            description="执行Shell命令",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "要执行的命令"},
                    "cwd": {"type": "string", "description": "工作目录（可选）"}
                },
                "required": ["command"]
            },
            handler=self._run_command,
            requires_confirmation=True
        ))

        # 搜索文件
        self.register(Tool(
            name="search_files",
            description="搜索文件（支持通配符）",
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "搜索模式，如 *.py, **/*.js"}
                },
                "required": ["pattern"]
            },
            handler=self._search_files
        ))

        # 搜索内容
        self.register(Tool(
            name="search_content",
            description="在文件中搜索内容（类似grep）",
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "搜索的文本或正则表达式"},
                    "path": {"type": "string", "description": "搜索路径，默认当前目录"},
                    "file_pattern": {"type": "string", "description": "文件类型过滤，如 *.py"}
                },
                "required": ["pattern"]
            },
            handler=self._search_content
        ))

        # 列出目录
        self.register(Tool(
            name="list_directory",
            description="列出目录内容",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "目录路径，默认当前目录"},
                    "show_hidden": {"type": "boolean", "description": "是否显示隐藏文件"}
                },
                "required": []
            },
            handler=self._list_directory
        ))

        # 获取当前目录
        self.register(Tool(
            name="get_current_dir",
            description="获取当前工作目录",
            parameters={"type": "object", "properties": {}, "required": []},
            handler=self._get_current_dir
        ))

    def register(self, tool: Tool):
        """注册工具"""
        self.tools[tool.name] = tool

    def get_openai_tools(self) -> List[Dict]:
        """获取 OpenAI 格式的工具列表"""
        return [tool.to_openai_format() for tool in self.tools.values()]

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """执行工具"""
        if tool_name not in self.tools:
            return ToolResult(success=False, output="", error=f"Unknown tool: {tool_name}")

        tool = self.tools[tool_name]
        return tool.execute(**arguments)

    def needs_confirmation(self, tool_name: str) -> bool:
        """检查工具是否需要确认"""
        if tool_name not in self.tools:
            return False
        return self.tools[tool_name].requires_confirmation

    # ========== 工具实现 ==========

    def _read_file(self, path: str) -> ToolResult:
        """读取文件"""
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return ToolResult(success=False, output="", error=f"File not found: {path}")
        
        # 检查文件大小
        size_mb = os.path.getsize(path) / (1024 * 1024)
        if size_mb > self.config.max_file_size_mb:
            return ToolResult(success=False, output="", 
                            error=f"File too large: {size_mb:.1f}MB > {self.config.max_file_size_mb}MB")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return ToolResult(success=True, output=content)
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(path, 'r', encoding='gbk') as f:
                    content = f.read()
                return ToolResult(success=True, output=content)
            except:
                return ToolResult(success=False, output="", error="Unable to decode file")

    def _write_file(self, path: str, content: str) -> ToolResult:
        """写入文件"""
        path = os.path.expanduser(path)
        
        # 创建目录
        dir_path = os.path.dirname(path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return ToolResult(success=True, output=f"Written to {path} ({len(content)} chars)")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def _edit_file(self, path: str, old_content: str, new_content: str) -> ToolResult:
        """编辑文件"""
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return ToolResult(success=False, output="", error=f"File not found: {path}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            if old_content not in content:
                return ToolResult(success=False, output="", 
                                error=f"Content not found in file")

            new_file_content = content.replace(old_content, new_content, 1)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_file_content)

            return ToolResult(success=True, 
                            output=f"Edited {path}: replaced {len(old_content)} chars with {len(new_content)} chars")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def _run_command(self, command: str, cwd: str = None) -> ToolResult:
        """执行Shell命令"""
        # 安全检查
        for blocked in self.config.blocked_commands:
            if blocked in command:
                return ToolResult(success=False, output="", 
                                error=f"Command blocked: contains '{blocked}'")

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd or os.getcwd(),
                timeout=30  # 30秒超时
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\n[STDERR]\n{result.stderr}"
            
            return ToolResult(
                success=result.returncode == 0,
                output=output,
                error="" if result.returncode == 0 else f"Exit code: {result.returncode}"
            )
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, output="", error="Command timed out (30s)")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def _search_files(self, pattern: str) -> ToolResult:
        """搜索文件"""
        try:
            matches = glob_module.glob(pattern, recursive=True)
            if not matches:
                return ToolResult(success=True, output="No files found")
            
            output = f"Found {len(matches)} files:\n" + "\n".join(matches)
            return ToolResult(success=True, output=output)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def _search_content(self, pattern: str, path: str = ".", file_pattern: str = "*") -> ToolResult:
        """搜索文件内容"""
        import re
        
        try:
            search_path = os.path.expanduser(path)
            results = []
            
            for root, dirs, files in os.walk(search_path):
                # 跳过隐藏目录
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    if glob_module.fnmatch.fnmatch(file, file_pattern):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                for i, line in enumerate(f, 1):
                                    if re.search(pattern, line, re.IGNORECASE):
                                        results.append(f"{file_path}:{i}: {line.rstrip()}")
                        except:
                            continue
            
            if not results:
                return ToolResult(success=True, output="No matches found")
            
            output = f"Found {len(results)} matches:\n" + "\n".join(results[:100])
            if len(results) > 100:
                output += f"\n... and {len(results) - 100} more matches"
            
            return ToolResult(success=True, output=output)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def _list_directory(self, path: str = ".", show_hidden: bool = False) -> ToolResult:
        """列出目录"""
        try:
            path = os.path.expanduser(path)
            if not os.path.exists(path):
                return ToolResult(success=False, output="", error=f"Path not found: {path}")

            items = []
            for item in os.listdir(path):
                if not show_hidden and item.startswith('.'):
                    continue
                
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path):
                    items.append(f"  [DIR] {item}/")
                else:
                    size = os.path.getsize(full_path)
                    items.append(f"  [FILE] {item} ({size} bytes)")

            if not items:
                return ToolResult(success=True, output="Empty directory")

            output = f"Directory: {path}\n" + "\n".join(items)
            return ToolResult(success=True, output=output)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def _get_current_dir(self) -> ToolResult:
        """获取当前目录"""
        return ToolResult(success=True, output=os.getcwd())
