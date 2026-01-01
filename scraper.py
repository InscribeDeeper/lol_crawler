"""
xdx.gg 爬虫 - 仅支持 NA 区域
使用 xdx.gg 替代 op.gg，HTML 结构更简洁清晰
"""
import re
import time
from typing import Dict, Tuple
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class XdxScraper:
    """xdx.gg 爬虫 - 仅支持 NA 区域"""
    
    def __init__(self):
        self.driver = self._init_chrome()
    
    def _init_chrome(self):
        """初始化 Chrome 浏览器"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        try:
            return webdriver.Chrome(options=options)
        except Exception as e:
            raise RuntimeError(f"无法启动 Chrome: {e}。请确保已安装 Chrome 和 ChromeDriver")
    
    def parse_username(self, username_input: str) -> Tuple[str, str]:
        """解析用户名: "karlphets#NA1" -> ("karlphets", "NA1")"""
        match = re.match(r'(.+?)\s*#(.+)', username_input)
        if not match:
            return (username_input.strip(), "NA1")
        return (match.group(1).strip(), match.group(2).strip().upper())
    
    def get_url(self, username: str, tag: str) -> str:
        """构建 xdx.gg URL"""
        # xdx.gg 格式: https://xdx.gg/username-tag
        name = f"{username}-{tag}".replace(' ', '-').lower()
        return f"https://xdx.gg/{name}"
    
    def scrape(self, username_input: str) -> Dict:
        """爬取账号数据"""
        username, tag = self.parse_username(username_input)
        url = self.get_url(username, tag)
        
        print(f"  访问: {url}")
        self.driver.get(url)
        time.sleep(3)  # 等待页面加载
        
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        return self._parse(soup, username, tag)
    
    def _parse(self, soup: BeautifulSoup, username: str, tag: str) -> Dict:
        """解析 HTML 提取数据 - 基于 xdx.gg 的清晰结构"""
        data = {
            'username': username,
            'tag': tag,
            'region': 'NA',
            'rank': 'Unranked',
            'tier': '',
            'win_rate': 0.0,
            'wins': 0,
            'losses': 0,
            'league_points': 0,
            'matches': []
        }
        
        # 查找 Solo/Duo 排位信息（单排）
        solo_rank = self._extract_solo_rank(soup)
        if solo_rank:
            data['rank'] = solo_rank['rank']
            data['tier'] = solo_rank['tier']
            data['win_rate'] = solo_rank['win_rate']
            data['wins'] = solo_rank['wins']
            data['losses'] = solo_rank['losses']
            data['league_points'] = solo_rank['lp']
        
        # 解析最近10场战绩
        data['matches'] = self._extract_matches(soup)
        
        # 解析最近90天游戏数据
        recent_90_days = self._extract_recent_90_days(soup)
        data['recent_90_days'] = recent_90_days
        
        # 提取上个赛季段位
        data['last_season_rank'] = self._extract_last_season_rank(soup)
        
        # 提取最近一局游戏的平均段位（作为隐藏分参考）
        data['last_match_avg_rank'] = self._extract_last_match_avg_rank(soup)
        
        return data
    
    def _extract_solo_rank(self, soup: BeautifulSoup) -> Dict:
        """提取 Solo/Duo 排位信息"""
        # 查找所有 SummonerRank_wrapper 容器
        rank_wrappers = soup.find_all('div', class_=re.compile(r'SummonerRank_wrapper', re.I))
        
        for wrapper in rank_wrappers:
            # 查找 rankicon 区域，检查是否是 Solo/Duo
            rankicon = wrapper.find('div', class_=re.compile(r'SummonerRank_rankicon', re.I))
            if not rankicon:
                continue
            
            # 检查是否是 Solo/Duo（单排）
            rankicon_text = rankicon.get_text(strip=True)
            if 'Solo/Duo' not in rankicon_text and 'Solo' not in rankicon_text:
                continue  # 跳过 Flex 等其他模式
            
            # 提取段位图标 alt 属性（如 "platinum"）
            img = rankicon.find('img')
            tier = img.get('alt', '').upper() if img else ''
            
            # 提取段位文字（如 "platinum I"）
            rank_div = wrapper.find('div', string=re.compile(r'\w+\s+[IVX\d]+', re.I))
            if not rank_div:
                # 尝试查找包含段位的 div
                rank_divs = wrapper.find_all('div')
                for div in rank_divs:
                    text = div.get_text(strip=True)
                    if re.match(r'\w+\s+[IVX\d]+', text, re.I):
                        rank_div = div
                        break
            
            if rank_div:
                rank_text = rank_div.get_text(strip=True)
                # 如果 tier 为空，从 rank_text 提取
                if not tier:
                    tier_match = re.match(r'(\w+)', rank_text, re.I)
                    if tier_match:
                        tier = tier_match.group(1).upper()
            
            # 提取统计信息
            stats_div = wrapper.find('div', class_=re.compile(r'SummonerRank_stats', re.I))
            if not stats_div:
                continue
            
            stats = self._extract_stats_from_div(stats_div)
            
            return {
                'tier': tier,
                'rank': rank_text if rank_div else tier,
                'lp': stats['lp'],
                'win_rate': stats['win_rate'],
                'wins': stats['wins'],
                'losses': stats['losses']
            }
        
        return None
    
    def _extract_stats_from_div(self, stats_div) -> Dict:
        """从统计 div 中提取数据"""
        stats = {'lp': 0, 'win_rate': 0.0, 'wins': 0, 'losses': 0}
        
        # 查找所有统计项 div
        stat_items = stats_div.find_all('div', recursive=False)
        
        for item in stat_items:
            text = item.get_text(strip=True)
            
            # 提取 LP
            if 'LP' in text:
                lp_match = re.search(r'(\d+)\s*LP', text, re.I)
                if lp_match:
                    stats['lp'] = int(lp_match.group(1))
            
            # 提取胜率
            if 'win rate' in text.lower() or '%' in text:
                winrate_match = re.search(r'(\d+\.?\d*)\s*%', text)
                if winrate_match:
                    stats['win_rate'] = float(winrate_match.group(1))
            
            # 提取胜场败场
            if 'W' in text and 'L' in text:
                # 格式: "188 W\n171 L" 或 "188 W 171 L"
                winloss_match = re.search(r'(\d+)\s*W.*?(\d+)\s*L', text, re.I)
                if winloss_match:
                    stats['wins'] = int(winloss_match.group(1))
                    stats['losses'] = int(winloss_match.group(2))
        
        return stats
    
    def _extract_recent_90_days(self, soup: BeautifulSoup) -> Dict:
        """提取最近90天游戏数据 - 简化版，只提取关键信息"""
        result = {
            'solo_duo_games': 0,
            'solo_duo_winrate': 0.0,
            'top_champion': '',
            'top_champion_pick': 0,
            'top_champion_winrate': 0.0
        }
        
        # 查找 "Last 90 Days Performance" 标题
        h3 = soup.find('h3', string=re.compile(r'Last 90 Days', re.I))
        if not h3:
            return result
        
        # 从标题后的容器中提取数据
        container = h3.find_next_sibling('div')
        if not container:
            return result
        
        # 提取 Solo/Duo 队列统计
        queue_divs = container.find_all('div', class_=re.compile(r'RecentStats_queue', re.I))
        for queue_div in queue_divs:
            queue_text = queue_div.get_text()
            if 'Solo/Duo' in queue_text:
                # 格式: <div>357 x</div><div>Solo/Duo</div><div>52.1%</div>
                divs = queue_div.find_all('div', recursive=False)
                if len(divs) >= 3:
                    games_text = divs[0].get_text(strip=True)  # "357 x"
                    winrate_text = divs[2].get_text(strip=True)  # "52.1%"
                    
                    games_match = re.search(r'(\d+)', games_text)
                    winrate_match = re.search(r'(\d+\.?\d*)%', winrate_text)
                    
                    if games_match:
                        result['solo_duo_games'] = int(games_match.group(1))
                    if winrate_match:
                        result['solo_duo_winrate'] = float(winrate_match.group(1))
                break
        
        # 提取最常用英雄（Pick 次数最多的，第一个）
        champion_rows = container.find_all('div', class_=re.compile(r'RecentStats_row', re.I))
        if champion_rows:
            top_row = champion_rows[0]
            
            # 英雄名称
            img = top_row.find('img', class_=re.compile(r'Champ_champ', re.I))
            if img:
                result['top_champion'] = img.get('alt', '')
            
            # Pick 次数和胜率
            divs = top_row.find_all('div', recursive=False)
            if len(divs) >= 5:
                pick_text = divs[2].get_text(strip=True)  # "165"
                winrate_text = divs[4].get_text(strip=True)  # "53%"
                
                if pick_text.isdigit():
                    result['top_champion_pick'] = int(pick_text)
                
                winrate_match = re.search(r'(\d+)%', winrate_text)
                if winrate_match:
                    result['top_champion_winrate'] = float(winrate_match.group(1))
        
        return result
    
    def _extract_recent_90_days(self, soup: BeautifulSoup) -> Dict:
        """提取最近90天游戏数据"""
        result = {
            'solo_duo_games': 0,
            'solo_duo_winrate': 0.0,
            'top_champion': '',
            'top_champion_pick': 0,
            'top_champion_winrate': 0.0
        }
        
        # 查找 "Last 90 Days Performance" 标题
        h3 = soup.find('h3', string=re.compile(r'Last 90 Days', re.I))
        if not h3:
            return result
        
        # 从标题后的容器中提取数据
        container = h3.find_next_sibling('div')
        if not container:
            return result
        
        # 提取 Solo/Duo 队列统计
        queue_divs = container.find_all('div', class_=re.compile(r'RecentStats_queue', re.I))
        for queue_div in queue_divs:
            queue_text = queue_div.get_text()
            if 'Solo/Duo' in queue_text:
                # 格式: <div>357 x</div><div>Solo/Duo</div><div>52.1%</div>
                divs = queue_div.find_all('div', recursive=False)
                if len(divs) >= 3:
                    games_text = divs[0].get_text(strip=True)  # "357 x"
                    winrate_text = divs[2].get_text(strip=True)  # "52.1%"
                    
                    games_match = re.search(r'(\d+)', games_text)
                    winrate_match = re.search(r'(\d+\.?\d*)%', winrate_text)
                    
                    if games_match:
                        result['solo_duo_games'] = int(games_match.group(1))
                    if winrate_match:
                        result['solo_duo_winrate'] = float(winrate_match.group(1))
                break
        
        # 提取最常用英雄（Pick 次数最多的）
        champion_rows = container.find_all('div', class_=re.compile(r'RecentStats_row', re.I))
        if champion_rows:
            # 第一个就是最常用的
            top_row = champion_rows[0]
            
            # 英雄名称
            img = top_row.find('img', class_=re.compile(r'Champ_champ', re.I))
            if img:
                result['top_champion'] = img.get('alt', '')
            
            # Pick 次数和胜率
            divs = top_row.find_all('div', recursive=False)
            if len(divs) >= 5:
                pick_text = divs[2].get_text(strip=True)  # "165"
                winrate_text = divs[4].get_text(strip=True)  # "53%"
                
                if pick_text.isdigit():
                    result['top_champion_pick'] = int(pick_text)
                
                winrate_match = re.search(r'(\d+)%', winrate_text)
                if winrate_match:
                    result['top_champion_winrate'] = float(winrate_match.group(1))
        
        return result
    
    def _extract_last_season_rank(self, soup: BeautifulSoup) -> str:
        """提取上个赛季段位"""
        # 查找包含上个赛季信息的元素
        # xdx.gg 可能在历史记录或特定区域显示上个赛季段位
        
        # 方法1: 查找包含 "Season" 或 "Last Season" 的元素
        season_keywords = ['last season', 'previous season', 'season', 's13', 's14', 's15']
        
        for keyword in season_keywords:
            # 查找包含关键词的文本节点
            elements = soup.find_all(string=re.compile(keyword, re.I))
            for elem in elements:
                # 查找父元素及其周围的文本
                parent = elem.parent
                if parent:
                    # 向上查找包含段位信息的容器
                    for _ in range(3):  # 最多向上查找3层
                        text = parent.get_text()
                        # 尝试提取段位
                        rank_match = re.search(r'(\w+\s+[IVX\d]+)', text, re.I)
                        if rank_match:
                            rank = rank_match.group(1)
                            # 验证是否是段位
                            if any(tier in rank.lower() for tier in ['iron', 'bronze', 'silver', 'gold', 'platinum', 'emerald', 'diamond', 'master', 'grandmaster', 'challenger']):
                                return rank
                        parent = parent.parent if parent.parent else None
                        if not parent:
                            break
        
        # 方法2: 查找历史段位区域（可能有特定的 class）
        history_sections = soup.find_all(['div', 'section'], class_=re.compile(r'history|season|previous|past', re.I))
        for section in history_sections:
            text = section.get_text()
            if any(keyword in text.lower() for keyword in ['season', 'last', 'previous']):
                # 尝试提取段位
                rank_match = re.search(r'(\w+\s+[IVX\d]+)', text, re.I)
                if rank_match:
                    rank = rank_match.group(1)
                    if any(tier in rank.lower() for tier in ['iron', 'bronze', 'silver', 'gold', 'platinum', 'emerald', 'diamond']):
                        return rank
        
        return ''
    
    def _extract_last_match_avg_rank(self, soup: BeautifulSoup) -> str:
        """提取最近一局游戏的平均段位（作为隐藏分参考）- 需要包含具体的 rank level，但不包含 LP"""
        # 查找最近一场比赛的详细信息
        # xdx.gg 可能在比赛详情中显示对手/队友的段位
        
        # 查找比赛记录容器
        match_containers = soup.find_all(['div', 'table'], class_=re.compile(r'match|game|history', re.I))
        
        for container in match_containers:
            # 查找第一场比赛（最近的）
            first_match = container.find(['tr', 'div', 'li'], class_=re.compile(r'match|game|item', re.I))
            if not first_match:
                continue
            
            # 在比赛详情中查找段位信息
            match_text = first_match.get_text()
            
            # 方法1: 查找 "Avg Rank" 或类似文本
            avg_patterns = [
                r'avg.*?rank.*?(\w+\s+[IVX]+)',
                r'average.*?rank.*?(\w+\s+[IVX]+)',
                r'rank.*?avg.*?(\w+\s+[IVX]+)',
            ]
            for pattern in avg_patterns:
                match = re.search(pattern, match_text, re.I)
                if match:
                    rank = match.group(1).strip()
                    if any(tier in rank.lower() for tier in ['iron', 'bronze', 'silver', 'gold', 'platinum', 'emerald', 'diamond']):
                        return rank
            
            # 方法2: 查找段位图标和对应的等级文本（罗马数字）
            rank_imgs = first_match.find_all('img', alt=re.compile(r'iron|bronze|silver|gold|platinum|emerald|diamond|master', re.I))
            if rank_imgs:
                for img in rank_imgs:
                    tier = img.get('alt', '')
                    if not tier:
                        continue
                    
                    # 查找图标附近的文本
                    parent = img.parent
                    for _ in range(3):
                        if not parent:
                            break
                        text = parent.get_text()
                        # 匹配 "tier + 罗马数字"，但后面不能紧跟着数字（可能是LP）
                        # 例如：匹配 "platinum I" 但不匹配 "platinum I79"
                        rank_pattern = rf'\b{tier}\s+([IVX]+)(?![0-9])'  # 负向前瞻，确保后面不是数字
                        match = re.search(rank_pattern, text, re.I)
                        if match:
                            return f"{tier} {match.group(1)}"
                        parent = parent.parent if parent.parent else None
            
            # 方法3: 查找完整的段位文本（段位 + 罗马数字等级，但不包含后面的数字LP）
            # 匹配模式：段位名称 + 空格 + 罗马数字（I, II, III, IV），后面不能是数字
            rank_pattern = r'\b(iron|bronze|silver|gold|platinum|emerald|diamond)\s+([IVX]+)(?![0-9])'
            matches = re.finditer(rank_pattern, match_text, re.I)
            for match in matches:
                tier = match.group(1)
                level = match.group(2)
                # 验证后面确实不是数字（可能是LP）
                end_pos = match.end()
                if end_pos < len(match_text):
                    next_char = match_text[end_pos:end_pos+1]
                    if next_char.isdigit():
                        continue  # 跳过，因为后面有数字（可能是LP）
                return f"{tier} {level}"
        
        return ''
    
    def _extract_matches(self, soup: BeautifulSoup) -> list:
        """提取最近10场战绩"""
        matches = []
        
        # 查找比赛记录容器 - xdx.gg 可能使用不同的 class
        # 尝试多种可能的选择器
        match_selectors = [
            {'class': re.compile(r'match|game|history|record', re.I)},
            {'class': re.compile(r'MatchHistory|GameHistory', re.I)},
        ]
        
        for selector in match_selectors:
            containers = soup.find_all(['div', 'table', 'ul'], selector)
            
            for container in containers:
                # 查找比赛行
                rows = container.find_all(['tr', 'div', 'li'], class_=re.compile(r'match|game|item|row', re.I))
                
                for row in rows[:10]:
                    match_data = self._extract_match_row(row)
                    if match_data and match_data['result'] != 'UNKNOWN':
                        matches.append(match_data)
                    
                    if len(matches) >= 10:
                        break
                
                if len(matches) >= 10:
                    break
            
            if len(matches) >= 10:
                break
        
        return matches[:10]
    
    def _extract_match_row(self, row) -> Dict:
        """从比赛行中提取数据"""
        match_data = {
            'champion': 'Unknown',
            'result': 'UNKNOWN',
            'kda': '0/0/0',
            'game_mode': 'Ranked Solo'
        }
        
        # 提取英雄名称
        img = row.find('img', class_=re.compile(r'champion', re.I))
        if img:
            match_data['champion'] = img.get('alt', 'Unknown')
        else:
            champ_elem = row.find(['div', 'span'], class_=re.compile(r'champion|name', re.I))
            if champ_elem:
                match_data['champion'] = champ_elem.get_text(strip=True)
        
        # 提取比赛结果
        result_elem = row.find(['div', 'span', 'td'], class_=re.compile(r'result|outcome|victory|defeat', re.I))
        if result_elem:
            result_text = result_elem.get_text(strip=True).lower()
            if 'win' in result_text or 'victory' in result_text:
                match_data['result'] = 'WIN'
            elif 'loss' in result_text or 'defeat' in result_text:
                match_data['result'] = 'LOSE'
        else:
            # 检查 class
            row_class = row.get('class', [])
            if any('win' in str(c).lower() or 'victory' in str(c).lower() for c in row_class):
                match_data['result'] = 'WIN'
            elif any('loss' in str(c).lower() or 'defeat' in str(c).lower() for c in row_class):
                match_data['result'] = 'LOSE'
        
        # 提取 KDA
        kda_elem = row.find(['div', 'span', 'td'], string=re.compile(r'\d+/\d+/\d+'))
        if kda_elem:
            match_data['kda'] = kda_elem.get_text(strip=True)
        else:
            number_elems = row.find_all(['div', 'span', 'td'], string=re.compile(r'\d+/\d+/\d+'))
            if number_elems:
                match_data['kda'] = number_elems[0].get_text(strip=True)
        
        return match_data
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
