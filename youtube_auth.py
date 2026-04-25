"""
YouTube 訂閱頻道一次性授權 + 抓取腳本
執行後會開啟瀏覽器讓你登入 Google，之後就不需要再做
"""
import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
CREDS_FILE    = Path("/Users/jimlin/.config/google-workspace-mcp/credentials.json")
YT_TOKEN_FILE = Path("/Users/jimlin/Downloads/claude/data/youtube_token.json")
YT_SUBS_FILE  = Path("/Users/jimlin/Downloads/claude/data/youtube_subs.json")


def get_yt_service():
    creds = None
    if YT_TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(YT_TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        YT_TOKEN_FILE.parent.mkdir(exist_ok=True)
        YT_TOKEN_FILE.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def fetch_subscriptions(service) -> list[dict]:
    subs = []
    page_token = None
    while True:
        resp = service.subscriptions().list(
            part="snippet",
            mine=True,
            maxResults=50,
            pageToken=page_token,
            order="alphabetical",
        ).execute()
        for item in resp.get("items", []):
            snippet = item["snippet"]
            subs.append({
                "channel": snippet["title"],
                "channel_id": snippet["resourceId"]["channelId"],
                "description": snippet.get("description", "")[:100],
            })
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return subs


def main():
    print("🔑 連線 YouTube...")
    service = get_yt_service()
    print("✅ 授權成功！")

    print("📺 抓取訂閱頻道...")
    subs = fetch_subscriptions(service)
    YT_SUBS_FILE.write_text(json.dumps(subs, ensure_ascii=False, indent=2))

    print(f"\n✅ 共 {len(subs)} 個訂閱頻道，已存到 data/youtube_subs.json")
    print("\n部分頻道：")
    for s in subs[:10]:
        print(f"  📺 {s['channel']}")


if __name__ == "__main__":
    main()
