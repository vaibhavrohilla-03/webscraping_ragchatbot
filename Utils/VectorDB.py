import os
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_core.retrievers import BaseRetriever
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from typing import List, Optional, Tuple, Any, Dict

class VectorDB:
    def __init__(self, embedding_model: str = 'models/text-embedding-004', persist_directory: Optional[str] = None):
        
        print(f"VectorDB initializing with embedding model: {embedding_model}") 
        
        google_api_key = os.getenv('GOOGLE_API_KEY')
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables.")

        try:
            self.embedding_model = GoogleGenerativeAIEmbeddings(
                model=embedding_model,
                google_api_key=google_api_key 
            )
        except Exception as e:
            print(f"Error initializing GoogleGenerativeAIEmbeddings: {e}")
            raise
            
        self.persist_directory = persist_directory
        self.collection_name = "document_collection"
        self.db: Optional[Chroma] = None # This will hold the Chroma DB instance
        
    def make_vector_db(self, documents: List[Document], chroma_upsert_batch_size: int = 4000) -> Optional[Chroma]:
        if not self.embedding_model:
            print("Embedding model not initialized. Cannot create vector DB.")
            return None
        if not documents:
            print("No documents provided to create vector database.")
            return None
            
        print(f"Initializing Chroma DB client for collection '{self.collection_name}' using {self.embedding_model.model}...")
        try:
            self.db = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embedding_model,
                persist_directory=self.persist_directory,
            )
        except Exception as e:
            print(f"Error initializing Chroma client: {e}")
            raise

        num_documents = len(documents)
        print(f"Adding {num_documents} documents to Chroma DB in batches of {chroma_upsert_batch_size}...")

        for i in range(0, num_documents, chroma_upsert_batch_size):

            batch_documents = documents[i:i + chroma_upsert_batch_size]
            current_batch_number = (i // chroma_upsert_batch_size) + 1
            total_batches = (num_documents + chroma_upsert_batch_size - 1) // chroma_upsert_batch_size
            
            print(f"Adding batch {current_batch_number}/{total_batches} with {len(batch_documents)} documents...")
            
            try:
                self.db.add_documents(documents=batch_documents)
            except Exception as e:
                print(f"Error adding batch {current_batch_number} of documents to Chroma: {e}")
                raise 
        if self.persist_directory:
            print(f"Chroma DB changes should be persisted to {self.persist_directory} automatically.")

        print(f"Vector database processing complete. {num_documents} documents processed into collection '{self.collection_name}'.")
        return self.db
            
    def load_vector_db(self) -> Optional[Chroma]:
        if not self.embedding_model:
            print("Embedding model not initialized. Cannot load vector DB.")
            return None
        if not self.persist_directory or not os.path.exists(self.persist_directory):
            print(f"Persist directory '{self.persist_directory}' not provided or doesn't exist.")
            return None
            
        print(f"Loading vector database from {self.persist_directory} using {self.embedding_model.model}...")
        
        try:
            self.db = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embedding_model, 
                persist_directory=self.persist_directory
            )
            print(f"Vector database loaded successfully.")
            return self.db
        except Exception as e:
            print(f"Error loading Chroma vector database from {self.persist_directory}: {e}")
            return None 
            
    def similarity_search(self, query: str, db: Chroma, k: int = 4 ) -> List[Document]:
        if not db: 
            print("No valid vector database (Chroma instance) provided for search.")
            return []
            
        print(f"Performing similarity search for: '{query}'")
        
        try:
            results = db.similarity_search(query, k=k)
            print(f"Found {len(results)} results.")
            return results
        except Exception as e:
            print(f"Error during similarity search: {e}")
            return []
            
    def similarity_search_with_score(self, query: str, k: int = 4) -> List[Tuple[Document, float]]:
        if not self.db:
            print("No vector database (self.db) loaded or created. Attempting to load...")
            if self.persist_directory and os.path.exists(self.persist_directory):
                self.load_vector_db()
                if not self.db:
                     print("Failed to load DB. Cannot perform search.")
                     return []
            else:
                print("No persist directory or DB not found. Cannot perform search.")
                return []
                
        print(f"Performing similarity search with score for: '{query}'")
        try:
            results = self.db.similarity_search_with_score(query, k=k)
            print(f"Found {len(results)} results.")
            return results
        except Exception as e:
            print(f"Error during similarity search with score: {e}")
            return []
            
    def get_retriever(self, search_kwargs: Optional[Dict[str, Any]] = None) -> Optional[BaseRetriever]:
        if not self.db:
            print("No vector database (self.db) loaded or created. Attempting to load...")
            if self.persist_directory and os.path.exists(self.persist_directory):
                self.load_vector_db()
                if not self.db:
                     print("Failed to load DB. Cannot get retriever.")
                     return None
            else:
                print("No persist directory or DB not found. Cannot get retriever.")
                return None
                
        if search_kwargs is None:
            search_kwargs = {"k": 4} 
            
        try:
            retriever = self.db.as_retriever(search_kwargs=search_kwargs)
            return retriever
        except Exception as e:
            print(f"Error creating retriever: {e}")
            return None
