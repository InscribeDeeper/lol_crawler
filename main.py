import sys
import time
import os
import math
import pandas as pd
from datetime import datetime
from scraper import XdxScraper


def read_names(file_path: str) -> list:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        print(f"错误: 文件 {file_path} 不存在")
        sys.exit(1)


def scrape_batch(names: list, output_file: str = None) -> pd.DataFrame:
    os.makedirs("output", exist_ok=True)
    if not output_file:
        filename = f"lol_accounts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    else:
        name, ext = os.path.splitext(os.path.basename(output_file))
        parts = name.split('_')
        has_timestamp = len(parts) >= 2 and len(parts[-1]) == 6 and parts[-1].isdigit() and len(parts[-2]) == 8 and parts[-2].isdigit()
        filename = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}" if not has_timestamp else f"{name}{ext}"
    output_file = os.path.join("output", filename)
    
    scraper = XdxScraper()
    results = []
    print(f"开始爬取 {len(names)} 个账号（NA 区域，使用 xdx.gg）...\n")
    
    try:
        for i, name in enumerate(names, 1):
            print(f"[{i}/{len(names)}] {name}")
            try:
                data = scraper.scrape(name)
                results.append(build_row(data))
                print(f"  ✓ {data['username']} - {data['rank']}")
            except Exception as e:
                print(f"  ✗ 失败: {e}")
                results.append(build_error_row(name))
            if i < len(names):
                time.sleep(3)
        
        df = pd.DataFrame(results)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n✓ 已保存: {output_file}")
        print(f"  成功: {len(df[df['Current Rank'] != 'ERROR'])}/{len(df)}")
        return df
    finally:
        scraper.close()


def get_wyang_status_indicator(rank: str) -> int:
    if not rank or rank == 'Unranked' or rank == 'ERROR':
        return 0
    rank_lower = rank.lower().strip()
    rank_map = {'diamond': 11, 'emerald 1': 10, 'emerald 2': 9, 'emerald 3': 8, 'emerald 4': 7, 'emerald i': 10, 'emerald ii': 9, 'emerald iii': 8, 'emerald iv': 7, 'platinum 1': 7, 'platinum 2': 6, 'platinum 3': 6, 'platinum 4': 5, 'plat 1': 7, 'plat 2': 6, 'plat 3': 6, 'plat 4': 5, 'platinum i': 7, 'platinum ii': 6, 'platinum iii': 6, 'platinum iv': 5, 'gold 1': 4, 'gold 2': 4, 'gold 3': 3, 'gold 4': 3, 'gold i': 4, 'gold ii': 4, 'gold iii': 3, 'gold iv': 3, 'silver': 2}
    if rank_lower in rank_map:
        return rank_map[rank_lower]
    if 'diamond' in rank_lower:
        return 11
    elif 'emerald' in rank_lower:
        return 10 if ('1' in rank_lower or 'i' in rank_lower) else (9 if ('2' in rank_lower or 'ii' in rank_lower) else (8 if ('3' in rank_lower or 'iii' in rank_lower) else (7 if ('4' in rank_lower or 'iv' in rank_lower) else 7)))
    elif 'platinum' in rank_lower or 'plat' in rank_lower:
        return 7 if ('1' in rank_lower or 'i' in rank_lower) else (6 if ('2' in rank_lower or 'ii' in rank_lower) else (6 if ('3' in rank_lower or 'iii' in rank_lower) else (5 if ('4' in rank_lower or 'iv' in rank_lower) else 5)))
    elif 'gold' in rank_lower:
        return 4 if ('1' in rank_lower or 'i' in rank_lower) else (4 if ('2' in rank_lower or 'ii' in rank_lower) else (3 if ('3' in rank_lower or 'iii' in rank_lower) else (3 if ('4' in rank_lower or 'iv' in rank_lower) else 3)))
    elif 'silver' in rank_lower:
        return 2
    return 0


def build_row(data: dict) -> dict:
    rank = data.get('rank', 'Unranked')
    recent_90 = data.get('recent_90_days', {})
    last_3_ranks_str = data.get('last_match_avg_rank', '')
    last_3_ranks = [r.strip() for r in last_3_ranks_str.split(',')] if last_3_ranks_str else []
    avg_score = sum(get_wyang_status_indicator(r) for r in last_3_ranks) / len(last_3_ranks) if last_3_ranks else 0
    return {
        'Account': data['username'], 'Current Rank': rank,
        'League Points': data.get('league_points', 0), 'Wyang - Rank Score': get_wyang_status_indicator(rank),
        'Win Rate %': data.get('win_rate', 0.0), 'Wins': data.get('wins', 0), 'Losses': data.get('losses', 0),
        'Games (90 days)': recent_90.get('solo_duo_games', 0),
        'Win Rate % (90 days)': recent_90.get('solo_duo_winrate', 0.0),
        'Last Season Rank': data.get('last_season_rank', ''),
        'Last 3 Matches Ranks': last_3_ranks_str,
        'Wyang - Hidden Rank Score (Last 3 Matches)': math.ceil(avg_score) if last_3_ranks else 0,
        'Win Rate % (Last 10)': data.get('recent_10_winrate', 0.0),
        'Win Rate % (Last 3)': data.get('recent_3_winrate', 0.0)
    }


def build_error_row(name: str) -> dict:
    username = name.strip() if '#' in name else f"{name.strip()}#NA1"
    return {
        'Account': username, 'Current Rank': 'ERROR',
        'League Points': 0, 'Wyang - Rank Score': 0, 'Win Rate %': 0.0, 'Wins': 0, 'Losses': 0,
        'Games (90 days)': 0, 'Win Rate % (90 days)': 0.0,
        'Last Season Rank': '', 'Last 3 Matches Ranks': '',
        'Wyang - Hidden Rank Score (Last 3 Matches)': 0,
        'Win Rate % (Last 10)': 0.0, 'Win Rate % (Last 3)': 0.0
    }


def main():
    if len(sys.argv) < 2:
        print("使用方法: python main.py <names.txt> [output.csv]")
        print("示例: python main.py names.txt")
        print("示例: python main.py names.txt accounts.csv")
        print("\n注意: CSV 文件会自动保存到 output/ 文件夹，文件名会自动添加时间戳")
        sys.exit(1)
    
    names = read_names(sys.argv[1])
    if not names:
        print("错误: 账号列表为空")
        sys.exit(1)
    
    try:
        df = scrape_batch(names, sys.argv[2] if len(sys.argv) > 2 else None)
        success = df[df['Current Rank'] != 'ERROR']
        if len(success) > 0:
            print("\n段位分布:")
            for rank, count in success['Current Rank'].value_counts().items():
                print(f"  {rank}: {count}")
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
