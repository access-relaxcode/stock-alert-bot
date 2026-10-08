from pathlib import Path

import os
import requests

import FinanceDataReader as fdr

webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

if not webhook_url:
    raise SystemExit(
        "디스코드 웹훅 주소가 설정되지 않았습니다.\n"
        "현재 터미널에서 DISCORD_WEBHOOK_URL을 설정한 뒤 다시 실행하세요."
    )

stock_name = "삼성전자"
stock_code = "005930"
target_price = 239999

try:
    data = fdr.DataReader(stock_code, "2026-09-01")
except requests.exceptions.RequestException:
    raise SystemExit(
        "주가 데이터를 요청하는 중 통신 오류가 발생했습니다. \n"
        "인터넷 연결을 확인하고 잠시 후 다시 실행하세요."
    )
if data.empty:
    raise SystemExit(
        "조회된 주가 데이터가 없습니다. \n"
        "종목 코드와 조회 시작 날짜를 확인하세요."
    )

price = data["Close"].iloc[-1]
price_date = data.index[-1].strftime("%Y-%m-%d")

record_path = Path(__file__).parent / "sent_alerts.txt"
alert_key = f"{stock_code}|{target_price}|{price_date}"

if record_path.exists():
    saved_records = record_path.read_text(encoding="utf-8")
else:
    saved_records = ""

print(f"조회 가격: {price:,.0f}원 / 설정 가격: {target_price:,.0f}원")
print(f"조건 판단 결과: {price >= target_price}")

if price >= target_price:
    if alert_key in saved_records.splitlines():
        print("동일한 조건과 날짜로 이미 알림을 보냈습니다.")
    else:
        message = (
            f"[가격 조건 충족] {stock_name}\n"
            f"데이터 기준일: {price_date}\n"
            f"종가: {price:,.0f}원 / 설정 가격: {target_price:,.0f}원"
        )
        print(message)

        try:
            
            response = requests.post(
                webhook_url,
                params={"wait": "true"},
                json={"content": message},
                timeout=10,
            )
            response.raise_for_status()

        except requests.exceptions.HTTPError:
            raise SystemExit(
                f"디스코드가 전송 요청을 거부했습니다. "
                f"상태 코드: {response.status_code}\n"
                "웹훅 주소와 디스코드 설정을 확인하세요."
            )

        except requests.exceptions.RequestException:
            raise SystemExit(
                "디스코드 전송 중 통신 오류가 발생했습니다.\n"
                "인터넷 연결을 확인하고 잠시 후 다시 실행하세요."
            )

        with record_path.open("a", encoding="utf-8") as file:
            file.write(alert_key + "\n")

        print("디스코드 전송 성공! 발송 기록을 저장했습니다.")
else:
    print(f"{stock_name}: 아직 설정 가격에 도달하지 않았습니다.")
