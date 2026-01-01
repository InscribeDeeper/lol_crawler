"""
主程序 - 批量爬取 op.gg 账号数据并导出 CSV
"""
import sys
import time
import os
import pandas as pd
from datetime import datetime
from scraper import XdxScraper


def read_names(file_path: str) -> list:
    """读取账号列表"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        print(f"错误: 文件 {file_path} 不存在")
        sys.exit(1)


def scrape_batch(names: list, output_file: str = None) -> pd.DataFrame:
    """批量爬取账号数据"""
    # 设置输出文件夹
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 处理输出文件名
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"lol_accounts_{timestamp}.csv"
    else:
        # 如果提供了文件名，检查是否已有时间戳
        name, ext = os.path.splitext(os.path.basename(output_file))
        # 检查文件名最后部分是否是时间戳格式（YYYYMMDD_HHMMSS）
        has_timestamp = False
        if '_' in name:
            parts = name.split('_')
            if len(parts) > 0:
                last_part = parts[-1]
                # 检查是否是时间戳格式（8位日期_6位时间，共15字符）
                if len(last_part) == 6 and last_part.isdigit():
                    # 检查前一个部分是否是8位日期
                    if len(parts) >= 2:
                        prev_part = parts[-2]
                        if len(prev_part) == 8 and prev_part.isdigit():
                            has_timestamp = True
        
        if not has_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}{ext}"
        else:
            filename = f"{name}{ext}"
    
    # 确保输出文件在 output 文件夹中
    output_file = os.path.join(output_dir, filename)
    
    scraper = XdxScraper()
    results = []
    
    print(f"开始爬取 {len(names)} 个账号（NA 区域，使用 xdx.gg）...\n")
    
    try:
        for i, name in enumerate(names, 1):
            print(f"[{i}/{len(names)}] {name}")
            
            try:
                data = scraper.scrape(name)
                row = build_row(data)
                results.append(row)
                print(f"  ✓ {data['username']} #{data['tag']} - {data['rank']}")
            except Exception as e:
                print(f"  ✗ 失败: {e}")
                results.append(build_error_row(name))
            
            if i < len(names):
                time.sleep(3)  # 延迟避免被反爬
        
        # 保存到 CSV
        df = pd.DataFrame(results)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"\n✓ 已保存: {output_file}")
        print(f"  成功: {len(df[df['rank'] != 'ERROR'])}/{len(df)}")
        
        return df
    finally:
        scraper.close()


def get_rank_score(rank: str) -> int:
    """根据段位映射表返回分数"""
    if not rank or rank == 'Unranked' or rank == 'ERROR':
        return 0
    
    rank_lower = rank.lower().strip()
    
    # 段位映射表
    rank_map = {
        'diamond': 11,
        'emerald 1': 10,
        'emerald 2': 9,
        'emerald 3': 8,
        'emerald 4': 7,
        'emerald i': 10,
        'emerald ii': 9,
        'emerald iii': 8,
        'emerald iv': 7,
        'platinum 1': 7,
        'platinum 2': 6,
        'platinum 3': 6,
        'platinum 4': 5,
        'plat 1': 7,
        'plat 2': 6,
        'plat 3': 6,
        'plat 4': 5,
        'platinum i': 7,
        'platinum ii': 6,
        'platinum iii': 6,
        'platinum iv': 5,
        'gold 1': 4,
        'gold 2': 4,
        'gold 3': 3,
        'gold 4': 3,
        'gold i': 4,
        'gold ii': 4,
        'gold iii': 3,
        'gold iv': 3,
        'silver': 2,
    }
    
    # 直接匹配
    if rank_lower in rank_map:
        return rank_map[rank_lower]
    
    # 模糊匹配
    if 'diamond' in rank_lower:
        return 11
    elif 'emerald' in rank_lower:
        if '1' in rank_lower or 'i' in rank_lower:
            return 10
        elif '2' in rank_lower or 'ii' in rank_lower:
            return 9
        elif '3' in rank_lower or 'iii' in rank_lower:
            return 8
        elif '4' in rank_lower or 'iv' in rank_lower:
            return 7
        return 7  # 默认 Emerald
    elif 'platinum' in rank_lower or 'plat' in rank_lower:
        if '1' in rank_lower or 'i' in rank_lower:
            return 7
        elif '2' in rank_lower or 'ii' in rank_lower:
            return 6
        elif '3' in rank_lower or 'iii' in rank_lower:
            return 6
        elif '4' in rank_lower or 'iv' in rank_lower:
            return 5
        return 5  # 默认 Platinum
    elif 'gold' in rank_lower:
        if '1' in rank_lower or 'i' in rank_lower:
            return 4
        elif '2' in rank_lower or 'ii' in rank_lower:
            return 4
        elif '3' in rank_lower or 'iii' in rank_lower:
            return 3
        elif '4' in rank_lower or 'iv' in rank_lower:
            return 3
        return 3  # 默认 Gold
    elif 'silver' in rank_lower:
        return 2
    
    return 0


def build_row(data: dict) -> dict:
    """构建数据行"""
    rank = data.get('rank', 'Unranked')
    row = {
        'username': data['username'],
        'tag': data['tag'],
        'rank': rank,
        'LP': data.get('league_points', 0),
        'rank_score': get_rank_score(rank),
        'win_rate': data.get('win_rate', 0.0),
        'wins': data.get('wins', 0),
        'losses': data.get('losses', 0)
    }
    
    # 添加最近90天数据
    recent_90 = data.get('recent_90_days', {})
    row['recent_90d_solo_duo_games'] = recent_90.get('solo_duo_games', 0)
    row['recent_90d_solo_duo_winrate'] = recent_90.get('solo_duo_winrate', 0.0)
    row['recent_90d_top_champion'] = recent_90.get('top_champion', '')
    row['recent_90d_top_champion_pick'] = recent_90.get('top_champion_pick', 0)
    row['recent_90d_top_champion_winrate'] = recent_90.get('top_champion_winrate', 0.0)
    
    # 添加上个赛季段位和最近一局平均段位
    row['last_season_rank'] = data.get('last_season_rank', '')
    row['last_match_avg_rank'] = data.get('last_match_avg_rank', '')
    
    # 计算最近10局和最近3局胜率
    matches = data.get('matches', [])[:10]
    if matches:
        # 最近10局胜率
        wins_10 = sum(1 for m in matches if m.get('result') == 'WIN')
        row['recent_10_winrate'] = round((wins_10 / len(matches)) * 100, 2) if matches else 0.0
        
        # 最近3局胜率
        matches_3 = matches[:3]
        wins_3 = sum(1 for m in matches_3 if m.get('result') == 'WIN')
        row['recent_3_winrate'] = round((wins_3 / len(matches_3)) * 100, 2) if matches_3 else 0.0
    else:
        row['recent_10_winrate'] = 0.0
        row['recent_3_winrate'] = 0.0
    
    return row


def build_error_row(name: str) -> dict:
    """构建错误行"""
    username, tag = name.split('#') if '#' in name else (name, 'NA1')
    row = {
        'username': username.strip(),
        'tag': tag.strip(),
        'rank': 'ERROR',
        'LP': 0,
        'rank_score': 0,
        'win_rate': 0.0,
        'wins': 0,
        'losses': 0,
        'recent_90d_solo_duo_games': 0,
        'recent_90d_solo_duo_winrate': 0.0,
        'recent_90d_top_champion': '',
        'recent_90d_top_champion_pick': 0,
        'recent_90d_top_champion_winrate': 0.0,
        'last_season_rank': '',
        'last_match_avg_rank': '',
        'recent_10_winrate': 0.0,
        'recent_3_winrate': 0.0
    }
    
    return row


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python main.py <names.txt> [output.csv]")
        print("示例: python main.py names.txt")
        print("示例: python main.py names.txt accounts.csv")
        print("\n注意: CSV 文件会自动保存到 output/ 文件夹，文件名会自动添加时间戳")
        sys.exit(1)
    
    names_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    names = read_names(names_file)
    if not names:
        print("错误: 账号列表为空")
        sys.exit(1)
    
    try:
        df = scrape_batch(names, output_file)
        
        # 显示统计
        success = df[df['rank'] != 'ERROR']
        if len(success) > 0:
            print("\n段位分布:")
            for rank, count in success['rank'].value_counts().items():
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
