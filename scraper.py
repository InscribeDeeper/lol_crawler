import re
import time
from typing import Dict, Tuple
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class XdxScraper:
    def __init__(self):
        options = Options()
        for arg in ['--headless', '--no-sandbox', '--disable-dev-shm-usage', '--window-size=1920,1080']:
            options.add_argument(arg)
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        try:
            self.driver = webdriver.Chrome(options=options)
        except Exception as e:
            raise RuntimeError(f"无法启动 Chrome: {e}。请确保已安装 Chrome 和 ChromeDriver")
    
    def parse_username(self, username_input: str) -> Tuple[str, str]:
        match = re.match(r'(.+?)\s*#(.+)', username_input)
        return (match.group(1).strip(), match.group(2).strip().upper()) if match else (username_input.strip(), "NA1")
    
    def get_url(self, username: str, tag: str) -> str:
        return f"https://xdx.gg/{f'{username}-{tag}'.replace(' ', '').lower()}"
    
    def scrape(self, username_input: str) -> Dict:
        username, tag = self.parse_username(username_input)
        print(f"  访问: {self.get_url(username, tag)}")
        self.driver.get(self.get_url(username, tag))
        time.sleep(3)
        return self._parse(BeautifulSoup(self.driver.page_source, 'html.parser'), username, tag)
    
    def _parse(self, soup: BeautifulSoup, username: str, tag: str) -> Dict:
        solo_rank = self._extract_solo_rank(soup)
        recent_90 = self._extract_recent_90_days(soup)
        winrates = self._extract_recent_winrates(soup)
        return {
            'username': f"{username}#{tag}", 'region': 'NA',
            'rank': solo_rank.get('rank', 'Unranked') if solo_rank else 'Unranked',
            'tier': solo_rank.get('tier', '') if solo_rank else '',
            'win_rate': solo_rank.get('win_rate', 0.0) if solo_rank else 0.0,
            'wins': solo_rank.get('wins', 0) if solo_rank else 0,
            'losses': solo_rank.get('losses', 0) if solo_rank else 0,
            'league_points': solo_rank.get('lp', 0) if solo_rank else 0,
            'matches': self._extract_matches(soup),
            'recent_90_days': recent_90,
            'last_season_rank': self._extract_last_season_rank(soup),
            'last_match_avg_rank': self._extract_last_3_matches_avg_rank(soup),
            'recent_10_winrate': winrates.get('recent_10_winrate', 0.0),
            'recent_3_winrate': winrates.get('recent_3_winrate', 0.0)
        }
    
    def _extract_solo_rank(self, soup: BeautifulSoup) -> Dict:
        for wrapper in soup.find_all('div', class_=re.compile(r'SummonerRank_wrapper', re.I)):
            rankicon = wrapper.find('div', class_=re.compile(r'SummonerRank_rankicon', re.I))
            if not rankicon or ('Solo/Duo' not in rankicon.get_text(strip=True) and 'Solo' not in rankicon.get_text(strip=True)):
                continue
            tier = (rankicon.find('img') or {}).get('alt', '').upper()
            rank_div = wrapper.find('div', string=re.compile(r'\w+\s+[IVX\d]+', re.I)) or next((d for d in wrapper.find_all('div') if re.match(r'\w+\s+[IVX\d]+', d.get_text(strip=True), re.I)), None)
            rank_text = rank_div.get_text(strip=True) if rank_div else ''
            tier = tier or (re.match(r'(\w+)', rank_text, re.I).group(1).upper() if re.match(r'(\w+)', rank_text, re.I) else '')
            stats_div = wrapper.find('div', class_=re.compile(r'SummonerRank_stats', re.I))
            if stats_div:
                stats = self._extract_stats_from_div(stats_div)
                return {'tier': tier, 'rank': rank_text or tier, **stats}
        return None
    
    def _extract_stats_from_div(self, stats_div) -> Dict:
        stats = {'lp': 0, 'win_rate': 0.0, 'wins': 0, 'losses': 0}
        for item in stats_div.find_all('div', recursive=False):
            text = item.get_text(strip=True)
            lp_match = re.search(r'(\d+)\s*LP', text, re.I)
            if lp_match:
                stats['lp'] = int(lp_match.group(1))
            winrate_match = re.search(r'(\d+\.?\d*)\s*%', text)
            if winrate_match and ('win rate' in text.lower() or '%' in text):
                stats['win_rate'] = float(winrate_match.group(1))
            winloss = re.search(r'(\d+)\s*W.*?(\d+)\s*L', text, re.I)
            if winloss and 'W' in text and 'L' in text:
                stats['wins'], stats['losses'] = int(winloss.group(1)), int(winloss.group(2))
        return stats
    
    def _extract_recent_90_days(self, soup: BeautifulSoup) -> Dict:
        h3 = soup.find('h3', string=re.compile(r'Last 90 Days', re.I))
        if not h3 or not (container := h3.find_next_sibling('div')):
            return {'solo_duo_games': 0, 'solo_duo_winrate': 0.0, 'top_champion': '', 'top_champion_pick': 0, 'top_champion_winrate': 0.0}
        result = {'solo_duo_games': 0, 'solo_duo_winrate': 0.0, 'top_champion': '', 'top_champion_pick': 0, 'top_champion_winrate': 0.0}
        for queue_div in container.find_all('div', class_=re.compile(r'RecentStats_queue', re.I)):
            if 'Solo/Duo' in queue_div.get_text():
                divs = queue_div.find_all('div', recursive=False)
                if len(divs) >= 3:
                    games_match = re.search(r'(\d+)', divs[0].get_text(strip=True))
                    winrate_match = re.search(r'(\d+\.?\d*)%', divs[2].get_text(strip=True))
                    result['solo_duo_games'] = int(games_match.group(1)) if games_match else 0
                    result['solo_duo_winrate'] = float(winrate_match.group(1)) if winrate_match else 0.0
                break
        champion_rows = container.find_all('div', class_=re.compile(r'RecentStats_row', re.I))
        if champion_rows:
            top_row = champion_rows[0]
            result['top_champion'] = (top_row.find('img', class_=re.compile(r'Champ_champ', re.I)) or {}).get('alt', '')
            divs = top_row.find_all('div', recursive=False)
            if len(divs) >= 5:
                result['top_champion_pick'] = int(divs[2].get_text(strip=True)) if divs[2].get_text(strip=True).isdigit() else 0
                winrate_match = re.search(r'(\d+)%', divs[4].get_text(strip=True))
                result['top_champion_winrate'] = float(winrate_match.group(1)) if winrate_match else 0.0
        return result
    
    def _extract_last_season_rank(self, soup: BeautifulSoup) -> str:
        for keyword in ['last season', 'previous season', 'season', 's13', 's14', 's15']:
            for elem in soup.find_all(string=re.compile(keyword, re.I)):
                parent = elem.parent
                for _ in range(3):
                    if not parent:
                        break
                    rank_match = re.search(r'(\w+\s+[IVX\d]+)', parent.get_text(), re.I)
                    if rank_match and any(tier in rank_match.group(1).lower() for tier in ['iron', 'bronze', 'silver', 'gold', 'platinum', 'emerald', 'diamond', 'master', 'grandmaster', 'challenger']):
                        return rank_match.group(1)
                    parent = parent.parent if parent.parent else None
        for section in soup.find_all(['div', 'section'], class_=re.compile(r'history|season|previous|past', re.I)):
            if any(kw in section.get_text().lower() for kw in ['season', 'last', 'previous']):
                rank_match = re.search(r'(\w+\s+[IVX\d]+)', section.get_text(), re.I)
                if rank_match and any(tier in rank_match.group(1).lower() for tier in ['iron', 'bronze', 'silver', 'gold', 'platinum', 'emerald', 'diamond']):
                    return rank_match.group(1)
        return ''
    
    def _extract_last_3_matches_avg_rank(self, soup: BeautifulSoup) -> str:
        match_divs = soup.find_all('div', class_=re.compile(r'Match_(?:defeat|victory)', re.I))
        if not match_divs:
            return ''
        ranks = []
        for match_div in match_divs[:3]:
            match_text = match_div.get_text()
            rank_found = False
            for match in re.finditer(r'\b(iron|bronze|silver|gold|platinum|emerald|diamond)\s+([IVX]+)(?![0-9])', match_text, re.I):
                if match.end() >= len(match_text) or not match_text[match.end()].isdigit():
                    ranks.append(f"{match.group(1)} {match.group(2)}")
                    rank_found = True
                    break
            if not rank_found:
                for img in match_div.find_all('img', alt=re.compile(r'iron|bronze|silver|gold|platinum|emerald|diamond', re.I)):
                    tier = img.get('alt', '')
                    if tier:
                        parent = img.parent
                        for _ in range(3):
                            if not parent:
                                break
                            match = re.search(rf'\b{tier}\s+([IVX]+)(?![0-9])', parent.get_text(), re.I)
                            if match:
                                ranks.append(f"{tier} {match.group(1)}")
                                rank_found = True
                                break
                            parent = parent.parent if parent.parent else None
                    if rank_found:
                        break
        return ', '.join(ranks) if ranks else ''
    
    def _extract_recent_winrates(self, soup: BeautifulSoup) -> Dict:
        match_divs = soup.find_all('div', class_=re.compile(r'Match_(?:defeat|victory)', re.I))
        if not match_divs:
            return {'recent_10_winrate': 0.0, 'recent_3_winrate': 0.0}
        matches_10, matches_3 = match_divs[:10], match_divs[:3]
        wins_10 = sum(1 for div in matches_10 if 'victory' in str(div.get('class', [])).lower())
        wins_3 = sum(1 for div in matches_3 if 'victory' in str(div.get('class', [])).lower())
        return {'recent_10_winrate': round((wins_10 / len(matches_10)) * 100, 2) if matches_10 else 0.0, 'recent_3_winrate': round((wins_3 / len(matches_3)) * 100, 2) if matches_3 else 0.0}
    
    def _extract_matches(self, soup: BeautifulSoup) -> list:
        matches = []
        for selector in [{'class': re.compile(r'match|game|history|record', re.I)}, {'class': re.compile(r'MatchHistory|GameHistory', re.I)}]:
            for container in soup.find_all(['div', 'table', 'ul'], selector):
                for row in container.find_all(['tr', 'div', 'li'], class_=re.compile(r'match|game|item|row', re.I))[:10]:
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
        img = row.find('img', class_=re.compile(r'champion', re.I))
        champion = img.get('alt', 'Unknown') if img else (row.find(['div', 'span'], class_=re.compile(r'champion|name', re.I)) and row.find(['div', 'span'], class_=re.compile(r'champion|name', re.I)).get_text(strip=True) or 'Unknown')
        result_elem = row.find(['div', 'span', 'td'], class_=re.compile(r'result|outcome|victory|defeat', re.I))
        result_text = result_elem.get_text(strip=True).lower() if result_elem else ''
        row_class = row.get('class', [])
        is_win = 'win' in result_text or 'victory' in result_text or any('win' in str(c).lower() or 'victory' in str(c).lower() for c in row_class)
        is_lose = 'loss' in result_text or 'defeat' in result_text or any('loss' in str(c).lower() or 'defeat' in str(c).lower() for c in row_class)
        result = 'WIN' if is_win else ('LOSE' if is_lose else 'UNKNOWN')
        kda_elem = row.find(['div', 'span', 'td'], string=re.compile(r'\d+/\d+/\d+'))
        kda_list = row.find_all(['div', 'span', 'td'], string=re.compile(r'\d+/\d+/\d+'))
        kda = kda_elem.get_text(strip=True) if kda_elem else (kda_list[0].get_text(strip=True) if kda_list else '0/0/0')
        return {'champion': champion, 'result': result, 'kda': kda, 'game_mode': 'Ranked Solo'}
    
    def close(self):
        if self.driver:
            self.driver.quit()
