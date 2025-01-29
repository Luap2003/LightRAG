import asyncio
import os
from typing import List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
import requests
from xml.etree import ElementTree

# Global variable for output directory
OUTPUT_DIR = "../pydantic_ai_docs"  # You can change this to any directory you want

async def crawl_sequential(urls: List[str]):
    print("\n=== Sequential Crawling with Session Reuse ===")
    browser_config = BrowserConfig(
        headless=True,
        # For better performance in Docker or low-memory environments:
        extra_args=["--disable-dev-shm-usage", "--no-sandbox"],
    )
    crawl_config = CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator()
    )
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Create the crawler (opens the browser)
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()
    try:
        session_id = "session1"  # Reuse the same session across all URLs
        for url in urls:
            result = await crawler.arun(
                url=url,
                config=crawl_config,
                session_id=session_id
            )
            if result.success:
                print(f"Successfully crawled: {url}")
                
                # Extract domain from URL (if needed)
                domain = url.replace('https://', '').replace('http://', '').split('/')[0]
                
                # Create a filename from the URL
                filename = url.replace('/', '_').replace(':', '_')
                
                # Save markdown content to file
                try:
                    with open(f"{OUTPUT_DIR}/{filename}_markdown.txt", "w", encoding="utf-8") as f:
                        f.write(result.markdown_v2.raw_markdown)
                    print(f"Saved to: {OUTPUT_DIR}/{filename}_markdown.txt")
                except Exception as e:
                    print(f"Failed to save file for {url}: {str(e)}")

                # You can also save the HTML content if needed
                try:
                    with open(f"{OUTPUT_DIR}/{filename}_html.txt", "w", encoding="utf-8") as f:
                        f.write(result.html)
                    print(f"Saved HTML to: {OUTPUT_DIR}/{filename}_html.txt")
                except Exception as e:
                    print(f"Failed to save HTML file for {url}: {str(e)}")

            else:
                print(f"Failed: {url} - Error: {result.error_message}")
    finally:
        # After all URLs are done, close the crawler (and the browser)
        await crawler.close()

def get_pydantic_ai_docs_urls():
    """
    Fetches all URLs from the Pydantic AI documentation.
    Uses the sitemap (https://ai.pydantic.dev/sitemap.xml) to get these URLs.
    
    Returns:
        List[str]: List of URLs
    """            
    sitemap_url = "https://ai.pydantic.dev/sitemap.xml"
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()
        
        # Parse the XML
        root = ElementTree.fromstring(response.content)
        
        # Extract all URLs from the sitemap
        # The namespace is usually defined in the root element
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [loc.text for loc in root.findall('.//ns:loc', namespace)]
        
        return urls
    except Exception as e:
        print(f"Error fetching sitemap: {e}")
        return []

async def main():
    urls = get_pydantic_ai_docs_urls()
    if urls:
        print(f"Found {len(urls)} URLs to crawl")
        await crawl_sequential(urls)
    else:
        print("No URLs found to crawl")

if __name__ == "__main__":
    asyncio.run(main())