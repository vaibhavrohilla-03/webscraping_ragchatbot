import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from collections import deque

class WebScraper:
    def __init__(self, base_url, max_depth=3, max_crawl_duration=None, max_pages_to_scrape=None):
        self.base_url = self._normalize_url(base_url)
        self.base_domain = urlparse(self.base_url).netloc
        self.max_depth = max_depth
        self.max_crawl_duration = max_crawl_duration
        self.max_pages_to_scrape = max_pages_to_scrape
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self.ignored_links = [
            "login", "signup", "register", "signin", "auth", "account", "cart", "checkout",
            "javascript:", "mailto:", "tel:", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".rar", ".exe", ".dmg", ".pkg",
            "twitter.com", "facebook.com", "instagram.com", "linkedin.com", 
            "youtube.com", "google.com/maps", "googleusercontent.com", "t.me", "whatsapp.com",
            "pinterest.com", "reddit.com", "vimeo.com", "flickr.com"
        ]
        self.ignored_extensions = [
            '.png', '.jpg', '.jpeg', '.gif', '.css', '.js',
            '.ico', '.svg', '.webp', '.mp4', '.mp3', '.avi', '.mov',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.tar', '.gz', '.rar', '.7z'
        ]
    def _normalize_url(self, url):
        parsed = urlparse(url)
        path = parsed.path
        if not path:
            path = '/'
        elif path != '/' and path.endswith('/'):
            path = path.rstrip('/')
        
        return parsed._replace(path=path, fragment='').geturl()

    def _fetch_page(self, url):
        try:
            headers = {'User-Agent': self.user_agent}
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' not in content_type:
                print(f"Skipping non-HTML content at {url} (Content-Type: {content_type})")
                return None
            return response
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error fetching {url}: {e}")
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error fetching {url}: {e}")
        except requests.exceptions.Timeout as e:
            print(f"Timeout fetching {url}: {e}")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
        return None

    def _should_ignore_link(self, url):
        if any(keyword in url.lower() for keyword in self.ignored_links):
            return True
        parsed_url = urlparse(url)
        if any(parsed_url.path.lower().endswith(ext) for ext in self.ignored_extensions):
            return True
        return False

    def _is_valid_link(self, link):
        try:
            parsed_link = urlparse(link)
            if parsed_link.scheme not in ['http', 'https']:
                return False
            
            if parsed_link.netloc != self.base_domain:
                return False
            
            return True
        except Exception:
            return False 

    def _extract_links_from_html(self, html_content, current_page_url):
        soup = BeautifulSoup(html_content, 'html.parser')
        links = set()
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href: 
                full_url = urljoin(current_page_url, href)
                normalized_url = self._normalize_url(full_url)
                
                if self._is_valid_link(normalized_url) and not self._should_ignore_link(normalized_url):
                    links.add(normalized_url)
        return links

    def _extract_text_from_html(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for tag_name in ['nav', 'footer', 'aside', 'script', 'style', 'header', 'form', 'button', 'iframe']:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        data = {'title': soup.title.string.strip() if soup.title and soup.title.string else '', 'sections': []}
        
        current_section_title = None
        current_section_text = []

        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'span', 'div']):
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                if current_section_title is not None and current_section_text: 
                    data['sections'].append({'section_title': current_section_title, 'text': ' '.join(current_section_text).strip()})
                    current_section_text = []
                current_section_title = element.get_text(separator=' ', strip=True)
            elif element.name in ['p', 'li'] or \
                 (element.name == 'div' and not element.find_all(['h1','h2','h3','h4','h5','h6','p','li','div'])) or \
                 (element.name == 'span' and element.get_text(strip=True)): 

                text = element.get_text(separator=' ', strip=True)
                if text:
                    current_section_text.append(text)
                if current_section_title is None and not data['sections'] and text:
                    current_section_title = "Introduction" 

        if current_section_title is not None and current_section_text:
            data['sections'].append({'section_title': current_section_title, 'text': ' '.join(current_section_text).strip()})
        elif not data['sections'] and current_section_text: 
             data['sections'].append({'section_title': "Content", 'text': ' '.join(current_section_text).strip()})

        if not data['sections']:
            body_text = soup.body.get_text(separator=' ', strip=True) if soup.body else ''
            if body_text:
                 data['sections'].append({'section_title': "Full Page Content", 'text': body_text})
        
        data['sections'] = [sec for sec in data['sections'] if sec['text']] 
        return data

    def save_page_to_jsonl(self, page_data):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_folder = os.path.join(script_dir, '..', 'Data')
        
        try:
            os.makedirs(data_folder, exist_ok=True)
        except (OSError, AttributeError): 
            data_folder = os.path.join(os.getcwd(), 'Data')
            os.makedirs(data_folder, exist_ok=True)
            print(f"Warning: Could not use relative path based on script location. Saving to: {data_folder}")

        file_path = os.path.join(data_folder, "scraped_data.jsonl")
        try:
            with open(file_path, 'a', encoding='utf-8') as file:
                file.write(json.dumps(page_data, ensure_ascii=False) + "\n")
        except IOError as e:
            print(f"Error saving data to {file_path}: {e}")

    def crawl_website(self, politeness_delay=1): 
        urls_to_visit = deque([(self.base_url, 0)])
        visited_urls = set()
        start_time = time.time()
        pages_scraped_count = 0
        print(f"Starting crawl for {self.base_url}...")
        if self.max_crawl_duration:
            print(f"Time limit: {self.max_crawl_duration} seconds")
        if self.max_pages_to_scrape:
            print(f"Page limit: {self.max_pages_to_scrape} pages")
        print(f"Max depth: {self.max_depth}")
        try:
            while urls_to_visit:
                if self.max_crawl_duration is not None and (time.time() - start_time) >= self.max_crawl_duration:
                    print(f"\nStopping crawl: Maximum duration of {self.max_crawl_duration} seconds reached.")
                    break

                if self.max_pages_to_scrape is not None and pages_scraped_count >= self.max_pages_to_scrape:
                    print(f"\nStopping crawl: Maximum number of {self.max_pages_to_scrape} pages scraped.")
                    break
                
                current_url, current_depth = urls_to_visit.popleft()

                normalized_url = self._normalize_url(current_url) 

                if normalized_url in visited_urls:
                    continue
                
                if current_depth > self.max_depth: 
                    print(f"Skipping {normalized_url}: Exceeds max depth ({current_depth} > {self.max_depth})")
                    continue
                
                if self._should_ignore_link(normalized_url):
                    visited_urls.add(normalized_url) 
                    continue
                visited_urls.add(normalized_url)

                print(f"\nProcessing (Depth: {current_depth}, Scraped: {pages_scraped_count}): {normalized_url}")
    
                response = self._fetch_page(normalized_url)
                if response and response.content: 
                    html_content = response.text
                    
                    structured_text = self._extract_text_from_html(html_content)
                    if structured_text['sections'] or structured_text['title']: 
                        page_data = {'url': normalized_url, 'depth': current_depth, **structured_text}
                        self.save_page_to_jsonl(page_data)
                        pages_scraped_count += 1
                        print(f"Successfully scraped and saved: {normalized_url} ({pages_scraped_count}/{self.max_pages_to_scrape if self.max_pages_to_scrape is not None else 'unlimited'} pages)")
                    else:
                        print(f"No meaningful text content extracted from {normalized_url}")
                    
                    if current_depth < self.max_depth: 
                        try:
                            new_links = self._extract_links_from_html(html_content, normalized_url)
                            for link in new_links:
                                if link not in visited_urls and link not in [item[0] for item in urls_to_visit]: 
                                    urls_to_visit.append((link, current_depth + 1))
                        except Exception as e:
                            print(f"Error extracting links from {normalized_url}: {e}")
                    
                    time.sleep(politeness_delay) 
                else:
                    print(f"Failed to fetch or no content for {normalized_url}")

        except KeyboardInterrupt:
            print("\nCrawl interrupted by user.")
        finally:
            elapsed_time = time.time() - start_time
            print(f"\nCrawl finished for {self.base_url}.")
            print(f"Total pages scraped: {pages_scraped_count}")
            print(f"Total URLs visited (or attempted): {len(visited_urls)}")
            print(f"Total time taken: {elapsed_time:.2f} seconds.")
            print(f"Data saved to 'Data/scraped_data.jsonl' (relative to script's parent or CWD).")
