import requests
from bs4 import BeautifulSoup
import time

def scrape_techcrunch(search_term="technology", max_articles=10):
    """
    Scrape TechCrunch articles with proper error handling and data extraction
    """
    try:
        url = f"https://techcrunch.com/?s={search_term.replace(' ', '+')}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        articles = []
        
        # Find all article containers
        article_containers = soup.find_all("div", class_="loop-card__content")
        
        if not article_containers:
            # Try alternative selectors
            article_containers = soup.find_all("article") or soup.find_all("div", class_="post-block")
        
        for container in article_containers[:max_articles]:
            article_data = extract_article_data(container)
            if article_data["title"] and article_data["title"] != "No Title":
                articles.append(article_data)
        
        return articles

    except Exception as e:
        print(f"❌ Scraping error: {str(e)}")
        return []

def extract_article_data(container):
    """
    Extract article data from a container element
    """
    article = {
        "title": "No Title",
        "link": "#",
        "author": "",
        "date": "",
        "image": "",
        "excerpt": ""
    }
    
    try:
        # Extract title - try multiple selectors
        title_selectors = [
            "h3.loop-card__title",
            "h2.loop-card__title", 
            "h3",
            "h2",
            ".post-title",
            ".entry-title"
        ]
        
        for selector in title_selectors:
            title_element = container.select_one(selector)
            if title_element:
                article["title"] = title_element.get_text(strip=True)
                break
        
        # Extract link
        link_element = container.find("a")
        if link_element and "href" in link_element.attrs:
            link = link_element["href"]
            if link.startswith("/"):
                link = "https://techcrunch.com" + link
            article["link"] = link
        
        # Extract author
        author_selectors = [
            "a.loop-card__author",
            ".author",
            ".byline",
            "[class*='author']"
        ]
        
        for selector in author_selectors:
            author_element = container.select_one(selector)
            if author_element:
                article["author"] = author_element.get_text(strip=True)
                break
        
        # Extract date/meta
        date_selectors = [
            ".loop-card__meta",
            ".post-date",
            ".date",
            "time",
            "[class*='date']"
        ]
        
        for selector in date_selectors:
            date_element = container.select_one(selector)
            if date_element:
                article["date"] = date_element.get_text(strip=True)
                break
        
        # Extract image
        image_selectors = [
            "figure.loop-card__figure img",
            "img",
            ".featured-image img"
        ]
        
        for selector in image_selectors:
            img_element = container.select_one(selector)
            if img_element and "src" in img_element.attrs:
                article["image"] = img_element["src"]
                break
        
        # If no image found, try previous sibling
        if not article["image"]:
            prev_element = container.find_previous("figure", class_="loop-card__figure")
            if prev_element:
                img = prev_element.find("img")
                if img and "src" in img.attrs:
                    article["image"] = img["src"]
        
        # Extract excerpt
        excerpt_selectors = [
            ".loop-card__excerpt",
            ".excerpt",
            ".post-excerpt",
            "p"
        ]
        
        for selector in excerpt_selectors:
            excerpt_element = container.select_one(selector)
            if excerpt_element:
                excerpt_text = excerpt_element.get_text(strip=True)
                if len(excerpt_text) > 20:
                    article["excerpt"] = excerpt_text[:200] + "..." if len(excerpt_text) > 200 else excerpt_text
                    break
    
    except Exception as e:
        pass  # Silent fail for individual articles
    
    return article

def scrape_hackernoon(search_term="AI"):
    """
    Legacy function for backward compatibility
    """
    # For now, just return TechCrunch results
    # You can implement actual HackerNoon scraping later
    return scrape_techcrunch(search_term)

# Test function
if __name__ == "__main__":
    articles = scrape_techcrunch("artificial intelligence", 5)
    for article in articles:
        print(f"Title: {article['title']}")
        print(f"Author: {article['author']}")
        print(f"Link: {article['link']}")
        print("---")