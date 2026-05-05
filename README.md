# QingCode - 由开源大模型驱动的AI编程助手

QingCode 是一个类似 Claude Code 的 AI 编程助手，但使用国产开源大模型（DeepSeek、GLM、Qwen等）作为后端。

## 特性

- 🤖 支持多种国产大模型（DeepSeek、GLM、Qwen）
- 📁 文件读写和编辑
- 🔍 代码搜索（类似grep）
- 💻 Shell命令执行
- 🔄 Agent循环（规划→执行→验证）
- 💬 交互式终端界面
- 🔒 安全的权限控制

## 安装

```bash
# 克隆仓库
git clone https://github.com/your-username/qingcode.git
cd qingcode

# 安装依赖
pip install -r requirements.txt
```

## 使用

### 基本使用

```bash
# 设置API Key（以DeepSeek为例）
export DEEPSEEK_API_KEY=your-api-key

# 启动交互模式
python qingcode.py

# 单次查询模式
python qingcode.py -p "帮我写一个快速排序算法"
```

### 命令行参数

```bash
# 指定模型
python qingcode.py --model deepseek-coder

# 指定API地址
python qingcode.py --base-url https://api.deepseek.com/v1

# 详细输出
python qingcode.py -v

# 自动确认所有操作
python qingcode.py -y
```

### 支持的模型

| 模型 | 命令 | 说明 |
|------|------|------|
| DeepSeek Chat | `--model deepseek-chat` | 通用对话 |
| DeepSeek Coder | `--model deepseek-coder` | 编程专用 |
| GLM-4 | `--provider openai --model glm-4` | 智谱AI |
| Qwen | `--provider openai --model qwen-max` | 通义千问 |
| GPT-4o | `--provider openai --model gpt-4o` | OpenAI |
| Claude | `--provider anthropic --model claude-3-5-sonnet-20241022` | Anthropic |

### 交互命令

```
/help          显示帮助
/exit          退出程序
/clear         清空对话
/reset         重置Agent
/history       显示对话历史
/model [name]  切换模型
/config        显示配置
/save          保存对话
/load <file>   加载对话
```

## 工具

QingCode 内置以下工具：

| 工具 | 说明 |
|------|------|
| `read_file` | 读取文件内容 |
| `write_file` | 创建或写入文件 |
| `edit_file` | 编辑文件中的特定内容 |
| `run_command` | 执行Shell命令 |
| `search_files` | 搜索文件（支持通配符） |
| `search_content` | 搜索文件内容（类似grep） |
| `list_directory` | 列出目录内容 |

## 配置

### 环境变量

```bash
# API Key
export DEEPSEEK_API_KEY=your-key
export OPENAI_API_KEY=your-key
export ANTHROPIC_API_KEY=your-key

# 模型配置
export QINGCODE_MODEL=deepseek-chat
export QINGCODE_PROVIDER=deepseek
export QINGCODE_BASE_URL=https://api.deepseek.com/v1
```

### 配置文件

在 `~/.qingcode/config.json` 中配置：

```json
{
  "llm": {
    "provider": "deepseek",
    "model": "deepseek-chat",
    "base_url": "https://api.deepseek.com/v1",
    "temperature": 0.7,
    "max_tokens": 4096
  },
  "tools": {
    "max_file_size_mb": 10,
    "blocked_commands": ["rm -rf /", "format"]
  },
  "agent": {
    "max_iterations": 50,
    "auto_confirm": false,
    "verbose": false
  }
}
```

## 示例

### 1. 创建新项目

```
>>> 帮我创建一个Python FastAPI项目，实现用户认证功能
```

### 2. 调试代码

```
>>> 这个函数报错了，帮我看看哪里有问题
```

### 3. 重构代码

```
>>> 帮我把这10个文件的配置统一到一个config.py
```

### 4. 写测试

```
>>> 为这个模块写单元测试，运行并修复失败的测试
```

## 安全性

- 修改文件前会请求确认
- 危险命令（如rm -rf）被阻止
- 文件大小限制（默认10MB）
- 可配置的权限控制

## 与 Claude Code 的对比

| 特性 | QingCode | Claude Code |
|------|----------|-------------|
| 模型 | 国产开源（DeepSeek等） | Claude |
| 价格 | 便宜 | 贵 |
| 编程能力 | 强（DeepSeek V4） | 最强 |
| 中文支持 | 原生支持 | 支持 |
| 开源 | ✅ | ❌ |

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 致谢

- DeepSeek - 提供强大的开源模型
- Anthropic - Claude Code 的设计理念启发
- Rich - 终端UI库
- OpenAI - API接口标准
