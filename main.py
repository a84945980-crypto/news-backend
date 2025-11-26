from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup

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
    base_url = f"https://search.naver.com/search.naver?where=news&query={keyword}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    response = requests.get(base_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    news_list = []
    items = soup.select(".news_area")[:5]
    
    for idx, item in enumerate(items):
        try:
            title_tag = item.select_one(".news_tit")
            title = title_tag.text
            link = title_tag['href']
            source = item.select_one(".info.press").text.replace("언론사 선정", "").strip()
            summary = item.select_one(".dsc_txt_wrap").text.strip()
            
            news_list.append({
                "id": f"{keyword}_{idx}",
                "keyword": keyword,
                "source": source,
                "title": title,
                "link": link,
                "summary": summary
            })
        except Exception:
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
