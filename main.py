import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from mailer import send_html_email

load_dotenv()

# 설정 로드
API_URL = os.getenv("SEBOARD_API_URL")
CAT_ID = os.getenv("SEBOARD_CATEGORY_ID")
DB_FILE = "last_post_id.txt"

def get_latest_posts():
    # 민호님이 찾으신 진짜 주소로 업데이트
    base_url = "https://seboard.site/v1/posts"
    params = {
        "categoryId": CAT_ID, 
        "page": 0, 
        "perPage": 20  # 찾으신 파라미터명으로 수정
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://seboard.site",
        "Referer": "https://seboard.site/community/notice"
    }

    try:
        res = requests.get(base_url, params=params, headers=headers, timeout=10)
        
        if res.status_code != 200:
            print(f"❌ 접속 실패 (상태 코드: {res.status_code})")
            return []
            
        # 응답 데이터 구조 확인 (보통 'content' 리스트 안에 게시글이 들어있음)
        data = res.json()
        return data.get('content', [])
        
    except Exception as e:
        print(f"⚠️ API 데이터 해석 오류: {e}")
        return []

def run_notifier():
    print(f"🚀 [{datetime.now().strftime('%H:%M:%S')}] SEBoard 새 공지 확인 중...")
    posts = get_latest_posts()
    if not posts: return

    # 1. 마지막 확인 ID 로드
    last_id = 0
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            line = f.read().strip()
            last_id = int(line) if line else 0

    # 2. 새 글 필터링 (가장 큰 postId가 최신글)
    new_posts = [p for p in posts if p['postId'] > last_id]

    if not new_posts:
        print("✅ 새로운 공지가 없습니다.")
        return

    # 3. 메일 본문 제작 (민호님 스타일 디자인)
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
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

    # 4. 발송 및 ID 업데이트
    if send_html_email(subject, content_html):
        print(f"📧 새 글 {len(new_posts)}건 메일 발송 완료!")
        with open(DB_FILE, "w") as f:
            # 리스트의 첫 번째 글이 가장 최신이므로 해당 ID 저장
            f.write(str(new_posts[0]['postId']))

if __name__ == "__main__":
    run_notifier()