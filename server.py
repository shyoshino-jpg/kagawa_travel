"""
香川県高松市 旅行プランナー — Flask + Claude API バックエンド

起動方法:
    export ANTHROPIC_API_KEY=your-key-here
    pip install -r requirements.txt
    python server.py

アクセス: http://localhost:5000
"""

import json
import os

import anthropic
from flask import Flask, Response, render_template, request, stream_with_context

app = Flask(__name__)

# ---------------------------------------------------------------------------
# System prompt (Japanese) — instructs Claude to return pure JSON
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
あなたは香川県高松市専門の旅行プランナーです。
旅行者の条件（日程・人数・予算・興味）に合わせ、実在するスポット・飲食店を使った \
リアルで実用的な旅行プランを作成します。

【必須ルール】
- 純粋なJSON のみを返してください。マークダウンのコードブロック（```）は使わないこと。
- 実在するスポット名・店名・住所を使用してください。
- 各スポットには移動手段・所要時間・入場料を含めてください。
- 地元民しか知らないヒントを各スポットに必ず入れてください。

【返すJSONの構造】
{
  "travel_plan": {
    "destination": "香川県高松市",
    "dates": "<入力された日程>",
    "travelers": <人数(整数)>,
    "budget": "<予算レベル>",
    "interests": ["<興味1>", ...],
    "itinerary": [
      {
        "day": 1,
        "date": "YYYY-MM-DD",
        "theme": "その日のテーマ（例：うどん三昧と庭園の朝）",
        "schedule": {
          "morning": {
            "spot": {
              "name": "観光スポット名",
              "description": "詳細説明（2〜3文）",
              "duration_minutes": 90,
              "admission": "大人 410円（例）",
              "transport_from_central": {
                "method": "JR高松駅から路面電車で15分（例）",
                "minutes": 15
              },
              "local_tip": "地元民だけが知る情報・コツ"
            },
            "note": "朝のおすすめの過ごし方・補足"
          },
          "lunch": {
            "name": "店名",
            "style": "料理スタイル（例：セルフ式釜玉うどん）",
            "price_per_person": "300〜600円",
            "address": "高松市〇〇町〇〇",
            "transport": "高松駅より徒歩10分（例）",
            "must_order": "絶対注文すべきメニュー",
            "tip": "混雑回避・予約の有無など実用アドバイス"
          },
          "afternoon": {
            "spot": {
              "name": "観光スポット名",
              "description": "詳細説明",
              "duration_minutes": 120,
              "admission": "大人 1,000円（例）",
              "transport_from_central": {
                "method": "移動手段",
                "minutes": 20
              },
              "local_tip": "地元のヒント"
            },
            "note": "午後のおすすめ補足"
          },
          "dinner": {
            "name": "店名",
            "style": "料理スタイル",
            "price_per_person": "3,000〜5,000円",
            "address": "住所",
            "transport": "アクセス方法",
            "must_order": "おすすめメニュー",
            "tip": "予約推奨かどうかなど"
          },
          "evening": {
            "spot": {
              "name": "夜のスポット名",
              "description": "説明",
              "duration_minutes": 60,
              "admission": "無料（例）",
              "transport_from_central": {
                "method": "移動手段",
                "minutes": 5
              },
              "local_tip": "夜ならではのヒント"
            },
            "note": "夜の過ごし方補足"
          }
        }
      }
    ],
    "free_time_tips": [
      {
        "title": "スキマ時間のヒント名",
        "description": "詳細説明",
        "location": "場所・最寄りスポット"
      }
    ],
    "local_tips": [
      "地元民のヒント（例：うどん屋は午前中が勝負。14時閉店が多い）"
    ],
    "packing_tips": [
      "持ち物アドバイス（例：うどん屋はセルフが多いので動きやすい服装で）"
    ]
  }
}
"""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/generate", methods=["POST"])
def generate_plan():
    """Stream a travel plan from Claude as Server-Sent Events."""
    data = request.get_json(silent=True)
    if not data:
        return {"error": "リクエストが不正です"}, 400

    start_date: str = data.get("start_date", "")
    end_date: str = data.get("end_date", "")
    travelers: int = int(data.get("travelers", 2))
    budget: str = data.get("budget", "中程度")
    interests: list[str] = data.get("interests", [])

    if not start_date:
        return {"error": "日程を入力してください"}, 400

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "サーバー設定エラー：ANTHROPIC_API_KEY が未設定です"}, 500

    # Build dates string
    if end_date and end_date != start_date:
        dates_str = f"{start_date}〜{end_date}"
    else:
        dates_str = start_date

    interests_str = "、".join(interests) if interests else "観光全般"

    user_message = (
        "以下の条件で香川県高松市の旅行プランを作成してください。\n\n"
        "【旅行条件】\n"
        f"- 日程：{dates_str}\n"
        f"- 旅行者数：{travelers}名\n"
        f"- 予算レベル：{budget}\n"
        f"- 興味・関心：{interests_str}\n\n"
        "各日程について、午前・午後・夜の観光スポット、おすすめランチ・ディナー、"
        "移動手段と所要時間を含めてJSON形式で返してください。"
        "スキマ時間のおすすめや地元の知恵も充実させてください。"
    )

    client = anthropic.Anthropic(api_key=api_key)

    def generate_stream():
        try:
            with client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=16000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"
        except anthropic.AuthenticationError:
            yield f"data: {json.dumps({'error': 'APIキーが無効です'})}\n\n"
        except anthropic.RateLimitError:
            yield f"data: {json.dumps({'error': 'レート制限に達しました。しばらく待ってから再試行してください'})}\n\n"
        except Exception as exc:  # noqa: BLE001
            yield f"data: {json.dumps({'error': str(exc)}, ensure_ascii=False)}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate_stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug, threaded=True)
