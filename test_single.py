"""
测试单个账号爬取 - 用于调试
"""
from scraper import XdxScraper
import json

def test_single_account(username_input: str):
    """测试爬取单个账号"""
    print(f"测试爬取账号: {username_input}\n")
    
    scraper = XdxScraper()
    try:
        data = scraper.scrape(username_input)
        
        print("\n" + "="*50)
        print("爬取结果:")
        print("="*50)
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        print("\n" + "="*50)
        print("关键信息:")
        print("="*50)
        print(f"用户名: {data['username']} #{data['tag']}")
        print(f"区域: {data['region']}")
        print(f"段位: {data['rank']}")
        print(f"胜率: {data['win_rate']}%")
        print(f"胜场: {data['wins']}")
        print(f"败场: {data['losses']}")
        print(f"比赛记录数: {len(data['matches'])}")
        
        if data['matches']:
            print("\n最近比赛:")
            for i, match in enumerate(data['matches'][:5], 1):
                print(f"  {i}. {match['champion']} - {match['result']} - {match['kda']}")
        
        return data
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        scraper.close()


if __name__ == '__main__':
    # 测试单个账号
    test_account = "karlphets#NA1"
    
    # 可以从命令行参数获取
    import sys
    if len(sys.argv) > 1:
        test_account = sys.argv[1]
    
    test_single_account(test_account)

