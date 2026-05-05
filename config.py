"""
QingCode 配置文件
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str = "deepseek"  # deepseek, openai, anthropic, local
    model: str = "deepseek-chat"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096


@dataclass
class ToolConfig:
    """工具配置"""
    allowed_commands: list = None
    blocked_commands: list = None
    max_file_size_mb: int = 10
    allowed_paths: list = None
    blocked_paths: list = None

    def __post_init__(self):
        if self.allowed_commands is None:
            self.allowed_commands = ["*"]  # 允许所有
        if self.blocked_commands is None:
            self.blocked_commands = ["rm -rf /", "format", "del /f /s /q"]
        if self.allowed_paths is None:
            self.allowed_paths = ["*"]
        if self.blocked_paths is None:
            self.blocked_paths = ["/etc", "/sys", "C:\\Windows\\System32"]


@dataclass
class AgentConfig:
    """Agent 配置"""
    max_iterations: int = 50
    max_context_tokens: int = 100000
    auto_confirm: bool = False
    verbose: bool = False


@dataclass
class QingCodeConfig:
    """QingCode 总配置"""
    llm: LLMConfig = None
    tools: ToolConfig = None
    agent: AgentConfig = None
    working_dir: str = "."
    config_file: str = "~/.qingcode/config.json"

    def __post_init__(self):
        if self.llm is None:
            self.llm = LLMConfig()
        if self.tools is None:
            self.tools = ToolConfig()
        if self.agent is None:
            self.agent = AgentConfig()


def load_config() -> QingCodeConfig:
    """加载配置"""
    config = QingCodeConfig()

    # 从环境变量读取
    if os.getenv("QINGCODE_API_KEY"):
        config.llm.api_key = os.getenv("QINGCODE_API_KEY")
    if os.getenv("QINGCODE_MODEL"):
        config.llm.model = os.getenv("QINGCODE_MODEL")
    if os.getenv("QINGCODE_PROVIDER"):
        config.llm.provider = os.getenv("QINGCODE_PROVIDER")
    if os.getenv("QINGCODE_BASE_URL"):
        config.llm.base_url = os.getenv("QINGCODE_BASE_URL")

    return config


# 预设配置
PRESET_CONFIGS = {
    "deepseek": LLMConfig(
        provider="deepseek",
        model="deepseek-chat",
        base_url="https://api.deepseek.com/v1"
    ),
    "deepseek-coder": LLMConfig(
        provider="deepseek",
        model="deepseek-coder",
        base_url="https://api.deepseek.com/v1"
    ),
    "glm": LLMConfig(
        provider="openai",
        model="glm-4",
        base_url="https://open.bigmodel.cn/api/paas/v4"
    ),
    "qwen": LLMConfig(
        provider="openai",
        model="qwen-max",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    ),
    "openai": LLMConfig(
        provider="openai",
        model="gpt-4o"
    ),
    "claude": LLMConfig(
        provider="anthropic",
        model="claude-3-5-sonnet-20241022"
    )
}
