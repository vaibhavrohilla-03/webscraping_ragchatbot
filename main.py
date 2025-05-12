from Utils.Splitter import Splitter
from Utils.WebScraper import WebScraper
from Utils.VectorDB import VectorDB
import os


# using this for just testing the vectordb cause running the app each time is really  a hassle 

# Define file paths
scraped_data_file = os.path.join(os.path.dirname(__file__), 'Data', 'scraped_data.jsonl')
persist_directory = os.path.join(os.path.dirname(__file__), 'Data', 'chroma_db')

def main():
    # Initialize our classes
    print("Initializing components...")
    splitter = Splitter(scraped_data_file)
    vector_db = VectorDB(persist_directory = persist_directory)
   
    # Step 1: Split JSONL into documents
    print("\nSplitting JSONL into documents...")
    documents = splitter.split_jsonl_to_doc()
    print(f"Created {len(documents)} documents total")
   
    if not documents:
        print("No documents to process. Exiting.")
        return
   
    # Step 2: Create vectordb
    print("\nCreating vectordb...")
    db = vector_db.make_vector_db(documents)

    
if __name__ == "__main__":
    main()