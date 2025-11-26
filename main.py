from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NewsItem(BaseModel):
    id: str
    keyword: str
    source: str
    title: str
    link: str
    summary: str

def scrape_naver_news(keyword: str):
    # 최신순(sort=1) 정렬 추가
    base_url = f"https://search.naver.com/search.naver?where=news&query={keyword}&sort=1"
    
    # ★ 중요: 네이버가 봇을 차단하지 않도록 '브라우저인 척' 하는 헤더 추가
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    response = requests.get(base_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    news_list = []
    # 네이버 뉴스 구조 선택자 (news_area 클래스 사용)
    items = soup.select(".news_area")[:7] # 7개까지 가져오기
    
    for idx, item in enumerate(items):
        try:
            title_tag = item.select_one(".news_tit")
            if not title_tag: continue
            
            title = title_tag.text
            link = title_tag['href']
            
            # 언론사
            source_tag = item.select_one(".info.press")
            source = source_tag.text.replace("언론사 선정", "").strip() if source_tag else "뉴스"
            
            # 요약
            summary_tag = item.select_one(".dsc_txt_wrap")
            summary = summary_tag.text.strip() if summary_tag else "요약 없음"
            
            news_list.append({
                "id": f"{keyword}_{idx}_{int(time.time())}",
                "keyword": keyword,
                "source": source,
                "title": title,
                "link": link,
                "summary": summary
            })
        except Exception as e:
            print(f"Error parsing item: {e}")
            continue
            
    return news_list

@app.get("/api/news")
def get_news(keyword: str):
    try:
        results = scrape_naver_news(keyword)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
