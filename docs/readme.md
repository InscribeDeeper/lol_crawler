# League of Legends 账号数据爬虫

使用 Selenium 爬取 op.gg 上的英雄联盟账号数据，并将数据导出为 CSV 文件。**仅支持 NA 区域**。

## 功能特性

- ✅ 使用 Selenium 爬取 op.gg，无需 API Key
- ✅ 批量获取账号数据（胜率、胜场、败场、段位、最近10场战绩）
- ✅ 使用 pandas 处理数据
- ✅ 导出为 CSV 文件，方便后续分析
- ✅ 支持从文件读取名字列表批量爬取

## 安装

### 使用 uv（推荐）

uv 是一个快速的 Python 包管理器，可以创建独立的虚拟环境，不会影响你现有的 conda 环境。

```bash
# 1. 安装 uv（如果还没有）
# Windows PowerShell
irm https://astral.sh/uv/install.ps1 | iex

# 或者使用 pip（在任何环境）
pip install uv

# 2. 创建虚拟环境并安装依赖
uv venv

# 3. 激活虚拟环境
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# Windows CMD
.venv\Scripts\activate.bat
# Linux/Mac
source .venv/bin/activate

# 4. 安装依赖
uv pip install -r requirements.txt

# 或者使用 uv sync（只安装依赖，不安装项目本身）
uv sync --no-install-project
```

**使用 uv 的优势：**
- ✅ 不会影响现有的 conda 环境
- ✅ 安装速度非常快
- ✅ 自动管理虚拟环境
- ✅ 依赖解析更准确

### 其他安装方式

<details>
<summary>使用 conda（点击展开）</summary>

```bash
# 创建 conda 环境
conda create -n lol_crawler python=3.10
conda activate lol_crawler

# 安装依赖
pip install -r requirements.txt
```
</details>

<details>
<summary>使用 pip（点击展开）</summary>

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```
</details>

### 安装 Chrome 浏览器和 ChromeDriver
   - 确保已安装 Chrome 浏览器
   - 下载 ChromeDriver: https://chromedriver.chromium.org/
   - 确保 ChromeDriver 在系统 PATH 中，或放在项目目录下
   - 或者使用 `webdriver-manager` 自动管理（可选）

## 使用方法

### 1. 准备名字列表文件

创建一个文本文件（如 `names.txt`），每行一个账号，格式如下：

```
karlphets#NA1
BadAppleSlayer #NA1
ShinoMakuya#NA1
```

支持两种格式：
- `username#tag`（无空格）
- `username #tag`（有空格）

**注意：仅支持 NA 区域的账号**

### 2. 批量爬取账号数据

**确保已激活虚拟环境**（如果使用 uv）：
```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# Windows CMD
.venv\Scripts\activate.bat
# Linux/Mac
source .venv/bin/activate
```

运行主程序：

```bash
# 使用默认输出文件名（带时间戳）
python main.py names.txt

# 指定输出文件名
python main.py names.txt output.csv
```

程序会：
- 读取名字列表文件
- 使用 Selenium 打开 Chrome 浏览器爬取每个账号的数据
- 将所有数据保存到 CSV 文件
- 显示爬取进度和统计信息

## CSV 文件格式

导出的 CSV 文件包含以下列：

**账号基本信息：**
- `username`: 用户名
- `tag`: Tag（如 NA1）
- `region`: 区域（固定为 NA）
- `rank`: 段位（如 "DIAMOND I", "GOLD III"）
- `tier`: 等级（如 DIAMOND, GOLD）
- `win_rate`: 胜率（百分比）
- `wins`: 胜场
- `losses`: 败场
- `total_matches`: 获取到的比赛数量

**最近10场战绩（每场包含4列）：**
- `match_1_champion` 到 `match_10_champion`: 英雄名称
- `match_1_result` 到 `match_10_result`: 比赛结果（WIN/LOSE）
- `match_1_kda` 到 `match_10_kda`: K/D/A 数据
- `match_1_game_mode` 到 `match_10_game_mode`: 游戏模式

## 项目结构

```
lol_crawler/
├── main.py          # 主程序入口，批量爬取并导出 CSV
├── scraper.py       # op.gg 爬虫模块（使用 Selenium）
├── names.txt        # 示例名字列表文件
├── requirements.txt # Python 依赖
└── readme.md        # 本文件
```

## 使用 pandas 处理数据

导出的 CSV 文件可以用 pandas 轻松处理：

```python
import pandas as pd

# 读取 CSV
df = pd.read_csv('lol_accounts_20231201_120000.csv')

# 查看基本信息
print(df[['username', 'tag', 'rank', 'win_rate', 'wins', 'losses']])

# 筛选特定段位
diamond_players = df[df['rank'].str.contains('DIAMOND', na=False)]

# 按胜率排序
sorted_df = df.sort_values('win_rate', ascending=False)

# 统计各段位人数
rank_counts = df['rank'].value_counts()
print(rank_counts)

# 筛选高胜率玩家
high_winrate = df[df['win_rate'] > 60]
high_winrate.to_csv('high_winrate_players.csv', index=False)
```

## 注意事项

1. **Chrome 和 ChromeDriver**：
   - 必须安装 Chrome 浏览器
   - ChromeDriver 版本需要与 Chrome 版本匹配
   - 如果遇到驱动问题，可以尝试使用 `webdriver-manager` 自动管理

2. **爬取频率**：
   - 程序在每次请求之间会等待 3 秒，避免请求过快
   - 如果遇到反爬虫，可以增加延迟时间

3. **仅支持 NA 区域**：当前版本仅支持北美（NA）服务器。

4. **账号必须存在**：如果账号不存在或未进行排位赛，会标记为 ERROR。

5. **网络问题**：如果遇到网络错误或超时，可以重新运行程序。

6. **页面结构变化**：op.gg 的页面结构可能会变化，如果爬取失败可能需要更新选择器。

## 示例

### 批量爬取

```bash
# 使用默认输出文件名（带时间戳）
python main.py names.txt

# 指定输出文件名
python main.py names.txt my_accounts.csv
```

### 处理数据

```python
import pandas as pd

# 读取数据
df = pd.read_csv('lol_accounts_20231201_120000.csv')

# 查看前5行
print(df.head())

# 筛选钻石及以上段位
high_rank = df[df['rank'].str.contains('DIAMOND|MASTER|GRANDMASTER|CHALLENGER', na=False)]

# 导出筛选结果
high_rank.to_csv('high_rank_players.csv', index=False)
```

## 故障排除

### ChromeDriver 问题

如果遇到 ChromeDriver 相关错误：

1. **检查 Chrome 版本**：
   ```bash
   chrome --version
   ```

2. **下载匹配的 ChromeDriver**：
   - 访问 https://chromedriver.chromium.org/
   - 下载与 Chrome 版本匹配的驱动

3. **使用 webdriver-manager（推荐）**：
   ```bash
   pip install webdriver-manager
   ```
   然后修改 `scraper.py` 使用 `webdriver-manager` 自动管理驱动。

### 爬取失败

如果某些账号爬取失败：

1. 检查账号是否存在
2. 检查网络连接
3. 尝试手动访问 op.gg 查看账号页面是否正常
4. 增加延迟时间（修改 `main.py` 中的 `time.sleep(3)`）

## 许可证

MIT License
