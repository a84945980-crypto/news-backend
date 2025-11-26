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

def scrape_daum_news(keyword):
    # 다음 뉴스 검색 (최신순: sort=recency)
    url = f"https://search.daum.net/search?w=news&q={keyword}&sort=recency"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_list = []
        # 다음 뉴스 리스트 아이템 선택자
        items = soup.select("ul.list_news > li")

        for idx, item in enumerate(items[:15]): # 15개까지
            try:
                # 제목 및 링크
                title_tag = item.select_one(".tit_main")
                if not title_tag: continue
                
                title = title_tag.text.strip()
                link = title_tag['href']
                
                # 언론사 (보통 '연합뉴스 | 1분전' 형태라서 | 앞부분만 자름)
                source_tag = item.select_one(".txt_info")
                source = source_tag.text.strip() if source_tag else "다음뉴스"
                if "|" in source:
                    source = source.split("|")[0].strip()
                
                # 요약
                summary_tag = item.select_one(".desc")
                summary = summary_tag.text.strip() if summary_tag else "요약 없음"

                news_list.append({
                    "id": f"{keyword}_{idx}_{int(time.time())}",
                    "keyword": keyword,
                    "source": source,
                    "title": title,
                    "link": link,
                    "summary": summary
                })
            except Exception:
                continue
                
        return news_list
    except Exception as e:
        print(f"Error scraping daum news: {e}")
        return []

@app.get("/api/news")
def get_news(keyword: str):
    try:
        results = scrape_daum_news(keyword)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
