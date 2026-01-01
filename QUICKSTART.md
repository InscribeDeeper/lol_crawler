# 快速开始运行

## 第一步：设置环境（如果还没做）

```powershell
# 创建虚拟环境并安装依赖
uv sync --no-install-project

# 或者分步操作：
# uv venv
# .\.venv\Scripts\Activate.ps1
# uv pip install -r requirements.txt
```

## 第二步：激活虚拟环境

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

激活后，命令行前面会显示 `(.venv)`。

## 第三步：运行程序

```powershell
# 使用默认输出文件名（会自动生成带时间戳的文件名）
python main.py names.txt

# 或者指定输出文件名
python main.py names.txt output.csv
```

## 完整示例

```powershell
# 1. 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 2. 运行爬虫
python main.py names.txt

# 3. 等待爬取完成，结果会保存为 CSV 文件
```

## 注意事项

- 确保已安装 Chrome 浏览器
- 确保 ChromeDriver 在 PATH 中或项目目录下
- 爬取过程可能需要一些时间（每个账号约 3-5 秒）
- 结果会保存为 `lol_accounts_YYYYMMDD_HHMMSS.csv` 格式的文件

