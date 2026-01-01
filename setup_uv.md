# 使用 uv 快速开始

## 安装 uv

### Windows (PowerShell)
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

### 或使用 pip（在任何环境）
```bash
pip install uv
```

## 设置项目

```bash
# 1. 创建虚拟环境
uv venv

# 2. 激活虚拟环境
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Windows CMD
.venv\Scripts\activate.bat

# Linux/Mac
source .venv/bin/activate

# 3. 安装依赖
uv pip install -r requirements.txt
```

或者使用 `uv sync --no-install-project`（只安装依赖，不安装项目本身）：
```bash
uv sync --no-install-project
```

## 运行程序

```bash
python main.py names.txt
```

## 常用命令

```bash
# 添加新依赖
uv add package-name

# 更新依赖
uv sync --upgrade

# 查看已安装的包
uv pip list

# 移除虚拟环境
rm -rf .venv  # Linux/Mac
rmdir /s .venv  # Windows
```

