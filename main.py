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

def scrape_google_news(keyword):
    # 구글 뉴스 RSS 주소 (한국어 설정)
    url = f"https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko"
    
    try:
        response = requests.get(url, timeout=10)
        # XML 파싱 (lxml 대신 기본 html.parser 사용 - 호환성 위해)
        soup = BeautifulSoup(response.content, features="xml")
        
        news_list = []
        items = soup.find_all("item")[:10] # 10개 가져오기
        
        for idx, item in enumerate(items):
            title = item.title.text
            link = item.link.text
            pub_date = item.pubDate.text
            source = item.source.text if item.source else "Google News"
            
            # 구글 RSS는 요약이 따로 없어서 제목이나 날짜로 대체
            summary = f"{source}에서 {pub_date[:16]}에 보도된 뉴스입니다."

            news_list.append({
                "id": f"{keyword}_{idx}_{int(time.time())}",
                "keyword": keyword,
                "source": source,
                "title": title,
                "link": link,
                "summary": summary
            })
            
        return news_list
        
    except Exception as e:
        print(f"Error scraping google news: {e}")
        return []

@app.get("/api/news")
def get_news(keyword: str):
    try:
        results = scrape_google_news(keyword)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
