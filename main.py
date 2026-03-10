import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from mailer import send_html_email

# 로컬 테스트 시 .env 파일을 읽어옵니다.
load_dotenv()

# 환경 설정
DB_FILE = "last_post_id.txt"
CAT_ID = os.getenv("SEBOARD_CATEGORY_ID", "1")

def get_latest_posts():
    base_url = "https://seboard.site/v1/posts"
    params = {
        "categoryId": CAT_ID, 
        "page": 0, 
        "perPage": 20
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://seboard.site",
        "Referer": "https://seboard.site/community/notice"
    }

    try:
        res = requests.get(base_url, params=params, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"❌ 접속 실패 (상태 코드: {res.status_code})")
            return []
        data = res.json()
        return data.get('content', [])
    except Exception as e:
        print(f"⚠️ API 접속 오류: {e}")
        return []

def run_notifier():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"🚀 [{now_str}] SEBoard 스케줄링 체크 시작...")
    
    posts = get_latest_posts()
    if not posts: 
        print("⚠️ 게시글 데이터를 가져오지 못했습니다.")
        return

    # 1. 마지막 확인 ID 로드
    last_id = 0
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            line = f.read().strip()
            last_id = int(line) if line else 0

    # 2. 새 글 필터링
    new_posts = [p for p in posts if p['postId'] > last_id]

    # --- [테스트 모드: 새 글이 없을 때 실행될 로직] ---
    if not new_posts:
        print("✅ 새 공지는 없지만, 스케줄러 확인 메일을 발송합니다.")
        test_subject = f"🧪 [정기 보고] 5분 주기 점검 완료 ({datetime.now().strftime('%H:%M')})"
        test_html = f"""
        <div style="font-family: 'Malgun Gothic', sans-serif; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
            <h3 style="color: #28a745;">✅ 스케줄러 정상 작동 중</h3>
            <p>현재 시각: <strong>{now_str}</strong></p>
            <p>새로운 공지가 없어 정기 점검 메일을 보냅니다.</p>
            <p style="font-size: 0.8em; color: #999;">확인이 완료되면 이 테스트 로직을 제거하세요.</p>
        </div>
        """
        send_html_email(test_subject, test_html)
        return 
    # ------------------------------------------------

    # 3. 실제 새 글이 있을 때 발송하는 로직
    subject = f"🔔 [SEBoard] 새로운 학과 공지 ({len(new_posts)}건)"
    content_html = f"""
    <div style="font-family: 'Malgun Gothic', sans-serif; max-width: 600px; margin: auto; border: 1px solid #ed1c24; padding: 20px; border-radius: 12px;">
        <h2 style="color: #ed1c24; border-bottom: 2px solid #ed1c24; padding-bottom: 10px;">📢 신규 학과 공지 알림</h2>
        <p style="color: #666; font-size: 0.9em;">확인 시각: {now_str}</p>
    """

    for post in new_posts:
        title = post.get('title', '제목 없음')
        author = post.get('author', {}).get('name', '익명')
        p_id = post.get('postId')
        link = f"https://seboard.site/posts/{p_id}"
        
        content_html += f"""
        <div style="margin-bottom: 15px; padding: 15px; background-color: #fffafa; border: 1px solid #ffebeb; border-radius: 8px;">
            <strong style="font-size: 1.1em; color: #333;">{title}</strong><br>
            <span style="color: #888; font-size: 0.85em;">작성자: {author}</span><br><br>
            <a href="{link}" style="color: #ed1c24; font-weight: bold; text-decoration: none;">👉 게시글 읽으러 가기</a>
        </div>
        """
    content_html += "</div>"

    # 발송 및 ID 업데이트
    if send_html_email(subject, content_html):
        print(f"📧 새 글 {len(new_posts)}건 메일 발송 완료!")
        with open(DB_FILE, "w") as f:
            f.write(str(new_posts[0]['postId']))

if __name__ == "__main__":
    run_notifier()