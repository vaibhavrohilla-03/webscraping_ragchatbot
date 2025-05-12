import sys
import os
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from Utils.VectorDB import VectorDB
from Utils.RAG import RAG      
from dotenv import load_dotenv

load_dotenv()

def load_vector_db(persist_directory=None):
    if persist_directory is None:
        persist_directory = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'Data', 
            'chroma_db'
        )
    vector_db = VectorDB(persist_directory=persist_directory)
    return vector_db.load_vector_db()

def get_llm():
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.7,
        max_output_tokens=2048,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    return llm

def chat_page():
    st.title("Chat with University Website Knowledge Base")

    try:
        vector_db = VectorDB(persist_directory=os.path.join(os.path.dirname(__file__), '..', 'Data', 'chroma_db'))
        db = vector_db.load_vector_db()
        if db is None: 
            st.error("Failed to load vector database. Please ensure it's prepared.")
            return
    except Exception as e:
        st.error(f"Failed to load vector database: {e}")
        return
    

    if 'rag_instance' not in st.session_state:
        st.session_state.rag_instance = RAG()
    rag = st.session_state.rag_instance 

    llm = get_llm()
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("Ask a question about the website"):
        st.session_state.messages.append({"role": "user", "content": prompt}) 
        with st.chat_message("user"): 
            st.markdown(prompt)
        
        retriever = vector_db.get_retriever()
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = rag.chat(
                    query=prompt, 
                    retriever=retriever, 
                    llm=llm,
                    include_history=True 
                )
                st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})

def main():
    st.sidebar.title("University Website Knowledge Base")
    
    app_mode = st.sidebar.selectbox(
        "Choose the App Mode",
        ["Chat", "Prepare Database"]
    )
    if app_mode == "Chat":
        chat_page()
    else:
        from PrepareDatabase import run_prepare_database_app
        run_prepare_database_app()

if __name__ == "__main__":
    main()