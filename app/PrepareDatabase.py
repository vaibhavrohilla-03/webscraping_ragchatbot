import sys
import os
import streamlit as st

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from Utils.WebScraper import WebScraper
from Utils.Splitter import Splitter
from Utils.VectorDB import VectorDB

def prepare_database(url: str, max_depth: int, max_crawl_duration: int | None, max_pages_to_scrape: int | None):

    base_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Data')
    os.makedirs(base_data_dir, exist_ok=True)

    scraped_data_file = os.path.join(base_data_dir, 'scraped_data.jsonl')
    persist_directory = os.path.join(base_data_dir, 'chroma_db')

    if os.path.exists(scraped_data_file):
        try:
            os.remove(scraped_data_file)
        except OSError:
            pass 

    scraper = WebScraper(
        base_url=url,
        max_depth=max_depth,
        max_crawl_duration=max_crawl_duration,
        max_pages_to_scrape=max_pages_to_scrape
    )
    scraper.crawl_website()

    if not os.path.exists(scraped_data_file) or os.path.getsize(scraped_data_file) == 0:
         return None 

    splitter = Splitter(scraped_data_file)
    documents = splitter.split_jsonl_to_doc()

    if not documents:
        return None

    vector_db_manager = VectorDB(persist_directory=persist_directory)
    db_instance = vector_db_manager.make_vector_db(documents)

    if db_instance:
        return db_instance 
    else:
        return None 

def run_prepare_database_app():
    
    st.title("Website Knowledge Base Preparation")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("Configuration")
        url = st.text_input("Enter the website URL to crawl:", placeholder="e.g., https://example.com")

        st.subheader("Scraper Settings")
        max_depth = st.number_input("Maximum Crawl Depth", min_value=0, value=2, step=1, help="Levels of links to follow (0=starting page only).")

        use_duration_limit = st.checkbox("Set Time Limit?", value=False)
        max_crawl_duration = None
        if use_duration_limit:
            max_crawl_duration = st.number_input("Max Crawl Duration (seconds)", min_value=1, value=60, step=10)

        use_page_limit = st.checkbox("Set Page Limit?", value=True)
        max_pages_to_scrape = None
        if use_page_limit:
            max_pages_to_scrape = st.number_input("Max Pages to Scrape", min_value=1, value=10, step=1)

        prepare_button = st.button("Prepare Knowledge Base", use_container_width=True)

    with col2:
        status_placeholder = st.empty()

        if prepare_button:
            if url:
                status_placeholder.empty()
                with status_placeholder.container():
                    with st.spinner("Preparing knowledge base... This may take a while."):
                        db_result = None 
                        try:
                            db_result = prepare_database(
                                url=url,
                                max_depth=max_depth,
                                max_crawl_duration=max_crawl_duration,
                                max_pages_to_scrape=max_pages_to_scrape
                            )

                            if db_result:
                                st.success("Knowledge base prepared successfully!")
                                st.balloons()
                            else:
                                st.error("Failed to prepare knowledge base. Check input URL and scraper limitations.")

                        except ModuleNotFoundError as e:
                             st.error(f"Import Error: Could not find module. Ensure project structure is correct.")
                             st.info("Expected structure: \nProjectRoot/\n - App/\n   - preparedatabase.py\n - Utils/\n   - WebScraper.py\n   - Splitter.py\n   - VectorDB.py")
                             st.exception(e)
                        except Exception as e:
                            st.error(f"An unexpected error occurred during preparation.")
                            st.exception(e) 
            else:
                 status_placeholder.warning("Please enter a URL to prepare the knowledge base.")


if __name__ == "__main__":
    run_prepare_database_app()