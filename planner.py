"""
香川県高松市 旅行プランナー
Takamatsu, Kagawa Travel Planner

Usage:
    python planner.py --dates "2026-05-01,2026-05-03" --travelers 2 --budget "中程度" --interests "グルメ,観光,自然"
"""

import argparse
import json
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Spot data
# ---------------------------------------------------------------------------

SPOTS = {
    "morning": {
        "観光": [
            {
                "name": "栗林公園",
                "description": "特別名勝に指定された日本最大級の大名庭園。朝の散歩に最適。",
                "duration_minutes": 90,
                "admission": "大人 410円",
                "transport_from_central": {"method": "路面電車・バス", "minutes": 15},
                "local_tip": "朝8時開園直後は人が少なく写真映え。北湖エリアの掬月亭での抹茶体験もおすすめ（別途500円）。",
            },
            {
                "name": "高松城跡（玉藻公園）",
                "description": "海に面した珍しい海城跡。朝の海風が清々しい。",
                "duration_minutes": 60,
                "admission": "大人 200円",
                "transport_from_central": {"method": "徒歩", "minutes": 5},
                "local_tip": "鯛を直接手で餌やりできる体験が人気。干潮時は堀の底まで見える。",
            },
        ],
        "自然": [
            {
                "name": "屋島",
                "description": "瀬戸内海を一望できるメサ型の台地。山頂まで車で行けるが遊歩道もある。",
                "duration_minutes": 120,
                "admission": "無料",
                "transport_from_central": {"method": "高松琴平電鉄（ことでん）＋シャトルバス", "minutes": 30},
                "local_tip": "早朝6時頃は雲海が出ることも。山頂の屋島寺は四国八十八箇所84番。",
            },
        ],
        "グルメ": [
            {
                "name": "丸亀町商店街（朝の散策）",
                "description": "400年の歴史を持つアーケード商店街。朝は静かで地元の雰囲気を味わえる。",
                "duration_minutes": 45,
                "admission": "無料",
                "transport_from_central": {"method": "徒歩", "minutes": 5},
                "local_tip": "朝7時台に開く老舗の天ぷらうどん屋に地元民が行列を作る。",
            },
        ],
    },
    "afternoon": {
        "観光": [
            {
                "name": "四国村（さぬきの郷土館）",
                "description": "四国各地から移築した古民家33棟を展示するオープンエアミュージアム。",
                "duration_minutes": 120,
                "admission": "大人 1,000円",
                "transport_from_central": {"method": "ことでん琴平線 屋島駅下車・徒歩5分", "minutes": 25},
                "local_tip": "ガラスばり美術館では塩田千春の作品常設展示。カフェでのさぬきうどんが絶品。",
            },
            {
                "name": "高松市歴史資料館",
                "description": "高松藩の歴史や松平家ゆかりの資料を展示。無料で入れる。",
                "duration_minutes": 60,
                "admission": "無料",
                "transport_from_central": {"method": "徒歩", "minutes": 10},
                "local_tip": "スタッフが非常に親切。無料ガイドツアーは要予約。",
            },
        ],
        "自然": [
            {
                "name": "瀬戸内海クルーズ（直島・豊島フェリー）",
                "description": "現代アートの島・直島へのフェリー。船上から瀬戸内の多島美を楽しめる。",
                "duration_minutes": 180,
                "admission": "フェリー往復 約2,000円＋島内施設別途",
                "transport_from_central": {"method": "高松港フェリー乗り場・徒歩10分", "minutes": 10},
                "local_tip": "直島は予約必須の施設多数。地中美術館は1週間前に予約を。",
            },
            {
                "name": "五色台",
                "description": "瀬戸内海を見渡す展望台と豊かな自然。ハイキングコースあり。",
                "duration_minutes": 150,
                "admission": "無料",
                "transport_from_central": {"method": "バス", "minutes": 40},
                "local_tip": "白峰展望台からの夕景が最高。ハイキング後は麓の日帰り温泉へ。",
            },
        ],
        "グルメ": [
            {
                "name": "かまたま屋敷（うどん巡り）",
                "description": "高松郊外のセルフうどん店を巡るローカル体験。1軒数百円で食べ歩き。",
                "duration_minutes": 120,
                "admission": "1食 200〜600円",
                "transport_from_central": {"method": "レンタカー推奨", "minutes": 20},
                "local_tip": "うどんタクシーというガイド付きタクシーサービスを使うと効率的。",
            },
        ],
        "アート": [
            {
                "name": "高松市美術館",
                "description": "国内外の近現代アートを収蔵。コレクション展は安価で観覧可能。",
                "duration_minutes": 90,
                "admission": "コレクション展 200円",
                "transport_from_central": {"method": "徒歩", "minutes": 8},
                "local_tip": "企画展のタイミングで行くと海外巡回展が安く見られることも。",
            },
        ],
    },
    "evening": {
        "観光": [
            {
                "name": "高松港周辺ナイトウォーク",
                "description": "ライトアップされた高松城と港の夜景。夕涼みの地元民も多い。",
                "duration_minutes": 60,
                "admission": "無料",
                "transport_from_central": {"method": "徒歩", "minutes": 5},
                "local_tip": "港の「takamatsu PORT SQUARE」でしばしばイベント開催。",
            },
        ],
        "グルメ": [
            {
                "name": "片原町〜兵庫町の居酒屋街",
                "description": "地元の人が集まる活気ある飲み屋街。骨付鶏や瀬戸内の魚を堪能。",
                "duration_minutes": 120,
                "admission": "予算：3,000〜5,000円/人",
                "transport_from_central": {"method": "徒歩", "minutes": 3},
                "local_tip": "骨付鶏は丸亀の「一鶴」が本家だが、高松にも支店あり。瀬戸内の鮮魚なら「魚籠」がおすすめ。",
            },
        ],
        "自然": [
            {
                "name": "屋島夕景展望",
                "description": "夕暮れ時の瀬戸内海が黄金色に染まる絶景ポイント。",
                "duration_minutes": 60,
                "admission": "無料",
                "transport_from_central": {"method": "ことでん＋シャトルバス", "minutes": 30},
                "local_tip": "日没1時間前に着くと光の変化が楽しめる。帰りのバスの時刻を事前確認のこと。",
            },
        ],
    },
}

RESTAURANTS = {
    "lunch": {
        "低予算": [
            {
                "name": "山越うどん",
                "style": "セルフうどん（釜玉発祥の店）",
                "price_per_person": "300〜600円",
                "address": "綾川町柏原2334",
                "transport": "ことでん琴平線 滝宮駅よりタクシー約10分",
                "must_order": "釜玉うどん（中）",
                "tip": "行列覚悟。11時前到着推奨。駐車場あり。",
            },
            {
                "name": "うどん本陣 山田家",
                "style": "格式ある古民家でいただく本格讃岐うどん",
                "price_per_person": "700〜1,200円",
                "address": "高松市牟礼町原631",
                "transport": "ことでん志度線 八栗口駅より徒歩5分",
                "must_order": "ざるうどん定食",
                "tip": "国の登録有形文化財の建物で食べる体験そのものが価値あり。",
            },
        ],
        "中程度": [
            {
                "name": "さか枝",
                "style": "地元民に愛されるセルフ系うどん・天ぷら充実",
                "price_per_person": "500〜900円",
                "address": "高松市番町5-2-23",
                "transport": "高松駅より徒歩15分",
                "must_order": "かけうどん＋揚げたての天ぷら数品",
                "tip": "平日昼は地元のサラリーマンで混雑。午前中は早めに行くと空いている。",
            },
            {
                "name": "鶴丸（海鮮丼）",
                "style": "瀬戸内の鮮魚を使った海鮮丼・定食",
                "price_per_person": "1,200〜2,000円",
                "address": "高松市北浜町 高松市場内",
                "transport": "高松駅より徒歩10分",
                "must_order": "瀬戸内海鮮丼",
                "tip": "早朝4時から開く市場食堂。朝食・早昼に最適。",
            },
        ],
        "高級": [
            {
                "name": "一鶴 高松店",
                "style": "讃岐名物・骨付鶏の老舗",
                "price_per_person": "2,000〜3,500円",
                "address": "高松市鍛冶屋町4-11",
                "transport": "高松駅より徒歩10分",
                "must_order": "おやどり（1本）＋ひなどり（1本）",
                "tip": "骨付鶏の焼き鳥文化を生み出した発祥の店。パンでスープを拭い取るのが地元流。",
            },
        ],
    },
    "dinner": {
        "低予算": [
            {
                "name": "居酒屋 はな",
                "style": "地元常連客が集まる大衆居酒屋",
                "price_per_person": "2,000〜3,000円",
                "address": "高松市兵庫町エリア",
                "transport": "高松駅より徒歩7分",
                "must_order": "刺身盛り合わせ、骨付鶏",
                "tip": "予約なしでも入れることが多い。店員さんに地元おすすめを聞くと親切に教えてくれる。",
            },
        ],
        "中程度": [
            {
                "name": "遊鶴",
                "style": "瀬戸内の魚介と地酒が揃う和食居酒屋",
                "price_per_person": "4,000〜6,000円",
                "address": "高松市常磐町エリア",
                "transport": "高松駅より徒歩10分",
                "must_order": "瀬戸内タコ刺し、鯛の塩焼き、讃岐の地酒",
                "tip": "予約推奨。香川の地酒「川鶴」「綾菊」を試して。",
            },
            {
                "name": "海鮮和食 あら井",
                "style": "地元漁師直送の鮮魚を使う料理屋",
                "price_per_person": "4,500〜7,000円",
                "address": "高松市北浜エリア",
                "transport": "高松駅より徒歩12分",
                "must_order": "おまかせ刺身＋土鍋ご飯",
                "tip": "季節の鮮魚が変わるので何度来ても楽しめる。カウンター席がおすすめ。",
            },
        ],
        "高級": [
            {
                "name": "御料理 堀川",
                "style": "讃岐の食材を使った現代和食のコース",
                "price_per_person": "12,000〜20,000円",
                "address": "高松市西の丸町エリア",
                "transport": "高松駅より徒歩10分",
                "must_order": "おまかせコース（季節限定）",
                "tip": "要予約・ドレスコードあり。讃岐の食材への深いこだわりが感動的。",
            },
        ],
    },
}

FREE_TIME_TIPS = [
    {
        "title": "うどん自販機",
        "description": "高松市内には24時間稼働のうどん自販機がいくつか存在。深夜の小腹満たしに。",
        "location": "宮武うどん自動販売機（丸亀町近く）",
    },
    {
        "title": "ことでんの旅",
        "description": "高松琴平電鉄（ことでん）の1日フリーパスで沿線のうどん屋を気まぐれ下車。1,500円で乗り放題。",
        "location": "高松築港駅",
    },
    {
        "title": "高松中央商店街",
        "description": "日本最長級アーケード商店街（約2.7km）。100円ショップからブランド店まで何でもある。雨の日も安心。",
        "location": "高松駅より徒歩5分",
    },
    {
        "title": "道の駅 源平の里むれ",
        "description": "瀬戸内の新鮮な魚介と地元農産物が集まる道の駅。産直価格でお土産調達に最適。",
        "location": "高松市牟礼町（ことでん八栗口駅近く）",
    },
    {
        "title": "高松市中央卸売市場（一般開放日）",
        "description": "毎月第2・第4土曜日は一般公開あり。新鮮な魚介を市場価格で購入できる。",
        "location": "高松市鶴市町",
    },
]

LOCAL_TIPS = [
    "うどん巡りは午前中がベスト。午後は閉店する店が多い（14時頃まで）。",
    "ことでんの1日フリー切符（1,500円）は高松築港駅と瓦町駅で購入可能。",
    "瀬戸内国際芸術祭（奇数年開催）の時期は島のアート施設が一斉オープン。2025年は開催年。",
    "レンタサイクルは高松駅前で1日1,000円〜。市内の移動はほぼ自転車でカバーできる。",
    "丸亀城・金刀比羅宮（こんぴらさん）は高松から電車で30〜50分。日帰り圏内。",
    "高松の地酒：川鶴酒造（観音寺）、綾菊酒造（綾川町）が地元で有名。",
    "おみやげ定番：和三盆糖、骨付鶏（冷凍）、いりこ（煮干し）、讃岐漆器。",
    "両替・ATMはコンビニ（セブン・ローソン）が便利。JR高松駅構内にも外貨両替機あり。",
]

# ---------------------------------------------------------------------------
# Plan generation
# ---------------------------------------------------------------------------

BUDGET_MAP = {
    "低": "低予算",
    "低予算": "低予算",
    "安い": "低予算",
    "中": "中程度",
    "中程度": "中程度",
    "普通": "中程度",
    "高": "高級",
    "高級": "高級",
    "贅沢": "高級",
}


def parse_dates(dates_str: str):
    parts = [d.strip() for d in dates_str.split(",")]
    if len(parts) == 1:
        start = datetime.strptime(parts[0], "%Y-%m-%d")
        return [start]
    start = datetime.strptime(parts[0], "%Y-%m-%d")
    end = datetime.strptime(parts[1], "%Y-%m-%d")
    days = []
    current = start
    while current <= end:
        days.append(current)
        current += timedelta(days=1)
    return days


def normalize_interests(interests_str: str):
    return [i.strip() for i in interests_str.split(",")]


def pick_spot(time_of_day: str, interests: list, used: set):
    for interest in interests:
        candidates = SPOTS.get(time_of_day, {}).get(interest, [])
        for spot in candidates:
            key = spot["name"]
            if key not in used:
                used.add(key)
                return spot
    # fallback: any spot not yet used
    for interest_spots in SPOTS.get(time_of_day, {}).values():
        for spot in interest_spots:
            if spot["name"] not in used:
                used.add(spot["name"])
                return spot
    return None


def pick_restaurant(meal: str, budget_key: str, used: set):
    priority = [budget_key, "中程度", "低予算", "高級"]
    seen_keys = []
    for key in priority:
        if key in seen_keys:
            continue
        seen_keys.append(key)
        for r in RESTAURANTS.get(meal, {}).get(key, []):
            if r["name"] not in used:
                used.add(r["name"])
                return r
    # all exhausted — allow re-use of any restaurant
    for key in priority:
        for r in RESTAURANTS.get(meal, {}).get(key, []):
            return r
    return None


def build_plan(dates_str: str, travelers: int, budget: str, interests_str: str) -> dict:
    days = parse_dates(dates_str)
    interests = normalize_interests(interests_str)
    budget_key = BUDGET_MAP.get(budget, "中程度")

    used_spots = set()
    used_restaurants = set()

    itinerary = []

    for i, day in enumerate(days):
        morning_spot = pick_spot("morning", interests, used_spots)
        afternoon_spot = pick_spot("afternoon", interests, used_spots)
        evening_spot = pick_spot("evening", interests, used_spots)

        lunch = pick_restaurant("lunch", budget_key, used_restaurants)
        dinner = pick_restaurant("dinner", budget_key, used_restaurants)

        day_plan = {
            "day": i + 1,
            "date": day.strftime("%Y-%m-%d"),
            "schedule": {
                "morning": {
                    "spot": morning_spot,
                    "note": "朝食はホテルか、うどん屋（8〜9時開店）で軽く済ませると時間を有効に使えます。",
                },
                "lunch": lunch,
                "afternoon": {
                    "spot": afternoon_spot,
                    "note": "昼食後は少し休憩してから移動するとペース配分がよくなります。",
                },
                "dinner": dinner,
                "evening": {
                    "spot": evening_spot,
                    "note": "夕食後の夜散歩も高松の楽しみ方のひとつです。",
                },
            },
        }
        itinerary.append(day_plan)

    return {
        "travel_plan": {
            "destination": "香川県高松市",
            "dates": dates_str,
            "travelers": travelers,
            "budget": budget,
            "budget_normalized": budget_key,
            "interests": interests,
            "itinerary": itinerary,
            "free_time_tips": FREE_TIME_TIPS,
            "local_tips": LOCAL_TIPS,
            "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        }
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="香川県高松市 旅行プランジェネレーター",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  python planner.py --dates "2026-05-01,2026-05-03" --travelers 2 --budget 中程度 --interests グルメ,観光
  python planner.py --dates "2026-08-10" --travelers 4 --budget 高級 --interests 自然,アート
        """,
    )
    parser.add_argument("--dates", required=True, help="日程 (例: 2026-05-01 または 2026-05-01,2026-05-03)")
    parser.add_argument("--travelers", type=int, required=True, help="旅行者数")
    parser.add_argument("--budget", required=True, help="予算レベル (低予算/中程度/高級)")
    parser.add_argument("--interests", required=True, help="興味カテゴリ（カンマ区切り: グルメ/観光/自然/アート）")
    parser.add_argument("--output", default="-", help="出力先ファイル (デフォルト: 標準出力)")
    parser.add_argument("--indent", type=int, default=2, help="JSONインデント幅")

    args = parser.parse_args()

    plan = build_plan(
        dates_str=args.dates,
        travelers=args.travelers,
        budget=args.budget,
        interests_str=args.interests,
    )

    output_json = json.dumps(plan, ensure_ascii=False, indent=args.indent)

    if args.output == "-":
        print(output_json)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"プランを {args.output} に保存しました。")


if __name__ == "__main__":
    main()
