import os
import json
from langchain_text_splitters import RecursiveJsonSplitter, RecursiveCharacterTextSplitter
from langchain_core.documents import Document

class Splitter:
    def __init__(self, input_file):
        self.input_file = input_file  
        self.splitter = RecursiveJsonSplitter(max_chunk_size=2000)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200
        )
        self.chunks = None
        self.docs = None
    
    def split_jsonl(self):
        if not os.path.exists(self.input_file):
            print(f"File not found: {self.input_file}")
            return []
        
        with open(self.input_file, 'r', encoding='utf-8') as infile:
            all_chunks = []
            for line in infile:
                try:
                    json_obj = json.loads(line)
                    chunks = self.splitter.split_json(json_obj)
                    all_chunks.extend(chunks)  
                except json.JSONDecodeError:
                    print(f"Invalid JSON line: {line}")
            
            self.chunks = all_chunks
            return self.chunks
   
    def split_jsonl_to_doc(self):
        if not os.path.exists(self.input_file):
            print(f"File not found: {self.input_file}")
            return []
       
        all_docs = []
        with open(self.input_file, 'r', encoding='utf-8') as infile:
            for line_num, line in enumerate(infile, 1):
                try:
                    json_obj = json.loads(line)
                    sections = json_obj.get('sections', [])
                    
                    text_sections = []
                    for section in sections:
                        if isinstance(section, dict) and 'text' in section:
                            text_sections.append(section['text'])
                    
                    full_text = "\n".join(text_sections).strip()
                    if not full_text:
                        print(f"No valid text content in JSON object: {json_obj.get('url', 'Unknown')}")
                        continue
                    
 
                    text_chunks = self.text_splitter.split_text(full_text)
                    

                    for chunk in text_chunks:
                        doc = Document(
                            page_content=chunk,
                            metadata={
                                "source": json_obj.get("url", "Unknown"),
                                "title": json_obj.get("title", "No Title")
                            }
                        )
                        all_docs.append(doc)
                    
                    print(f"Processed line {line_num}: Created {len(text_chunks)} documents")
                    
                except json.JSONDecodeError:
                    print(f"Invalid JSON line {line_num}: {line[:50]}...")
                except Exception as e:
                    print(f"Unexpected error while processing line {line_num}: {str(e)}")
       
        self.docs = all_docs
        return all_docs
    
    def get_chunk_count(self):
        if self.chunks is None:
            return 0
        return len(self.chunks)