import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from mailer import send_html_email

# .env 파일 로드 (로컬 테스트용)
load_dotenv()

# 설정 로드 (GitHub Actions 실행 시에는 Secrets에서 환경변수를 가져옴)
API_URL = os.getenv("SEBOARD_API_URL", "https://seboard.site/v1/posts")
CAT_ID = os.getenv("SEBOARD_CATEGORY_ID", "1")
DB_FILE = "last_post_id.txt"

def get_latest_posts():
    """SEBoard API에서 최신 게시글 목록을 가져옵니다."""
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
        res = requests.get(API_URL, params=params, headers=headers, timeout=10)
        if res.status_code != 200:
            print(f"❌ 접속 실패 (상태 코드: {res.status_code})")
            return []
            
        data = res.json()
        return data.get('content', [])
        
    except Exception as e:
        print(f"⚠️ API 데이터 해석 오류: {e}")
        return []

def run_notifier():
    print(f"🚀 [{datetime.now().strftime('%H:%M:%S')}] SEBoard 시스템 테스트 시작...")
    posts = get_latest_posts()
    
    if not posts:
        print("❌ 게시글 데이터를 가져오지 못했습니다.")
        return

    # --- [테스트를 위한 강제 발송 설정] ---
    # 실제 운영 시에는 last_id와 비교하지만, 지금은 무조건 최신글 1개를 보냅니다.
    new_posts = posts[:1] 
    print(f"🛠️ 테스트 모드: 최신글 ID {new_posts[0].get('postId')}를 메일로 발송합니다.")
    # -------------------------------------

    # 메일 본문 제작
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    subject = f"🧪 [시스템 테스트] SEBoard 알림 노드 가동 보고"
    
    content_html = f"""
    <div style="font-family: 'Malgun Gothic', sans-serif; max-width: 600px; margin: auto; border: 1px solid #004a95; padding: 20px; border-radius: 12px;">
        <h2 style="color: #004a95; border-bottom: 2px solid #004a95; padding-bottom: 10px;">✅ 시스템 연결 테스트 완료</h2>
        <p style="color: #666; font-size: 0.9em;">테스트 시각: {now_str}</p>
        <p>이 메일이 도착했다면 <strong>GitHub Actions</strong>와 <strong>SMTP 메일 서버</strong> 연결이 성공한 것입니다.</p>
    """

    for post in new_posts:
        title = post.get('title', '제목 없음')
        author = post.get('author', {}).get('name', '익명')
        p_id = post.get('postId')
        link = f"https://seboard.site/posts/{p_id}"
        
        content_html += f"""
        <div style="margin-bottom: 15px; padding: 15px; background-color: #f0f7ff; border: 1px solid #d0e3ff; border-radius: 8px;">
            <strong style="font-size: 1.1em; color: #333;">최신글: {title}</strong><br>
            <span style="color: #888; font-size: 0.85em;">작성자: {author}</span><br><br>
            <a href="{link}" style="color: #004a95; font-weight: bold; text-decoration: none;">👉 실제 게시글 링크 확인</a>
        </div>
        """

    content_html += """
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="font-size: 0.8em; color: #999; text-align: center;">본 메일은 민호님의 SEBoard-Node 테스트 자동화 노드에서 발송되었습니다.</p>
    </div>
    """

    # 발송 실행
    if send_html_email(subject, content_html):
        print(f"📧 테스트 메일 발송 완료!")
        # 테스트 중에는 파일 업데이트를 하지 않아도 됩니다 (계속 테스트 가능하도록)
    else:
        print("❌ 메일 발송에 실패했습니다. 비밀번호나 설정을 확인하세요.")

if __name__ == "__main__":
    run_notifier()