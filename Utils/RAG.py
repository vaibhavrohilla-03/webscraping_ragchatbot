# Utils/RAG.py
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from typing import Any, Optional, Union, List
from operator import itemgetter 

class RAG:
    def __init__(self):
        self.chat_history: List[Union[AIMessage, HumanMessage]] = []
        
    @staticmethod
    def getprocessedcontent(docs):
        processed_content = "\n\n".join([doc.page_content for doc in docs])
        return processed_content
    
    @staticmethod
    def create_prompt(template: str) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_template(template)
    
    @staticmethod
    def create_chain(retriever: Any, llm: Any, prompt: ChatPromptTemplate, 
                     content: Optional[str] = None) -> Any: 
        
        if content is not None: 
            rag_chain = (
                {"context": lambda _: content, "question": RunnablePassthrough()} 
                | prompt
                | llm 
                | StrOutputParser()
            )
        else:
            retrieval_chain = itemgetter("question") | retriever | RAG.getprocessedcontent
            rag_chain = RunnablePassthrough.assign(
                context=retrieval_chain 
            ) | prompt | llm | StrOutputParser()
            
        return rag_chain
    
    def create_contextualize_chain(self, llm: Any) -> Any:
        contextualize_q_system_prompt = """
        Given a chat history and the latest user question
        which might reference context in the chat history,
        formulate a standalone question which can be understood
        without the chat history. Do NOT answer the question,
        just reformulate it if needed and otherwise return it as is.
        """
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        contextualize_chain = contextualize_q_prompt | llm | StrOutputParser()
        
        return contextualize_chain
    
    def get_formatted_messages(self):
        return [msg for msg in self.chat_history if isinstance(msg, HumanMessage) or isinstance(msg, AIMessage)]
    
    def get_formatted_history_str(self):
        history_str = ""
        for msg in self.chat_history[:-1]:
            if isinstance(msg, HumanMessage):
                history_str += f"Human: {msg.content}\n"
            elif isinstance(msg, AIMessage):
                history_str += f"AI: {msg.content}\n"
        return history_str.strip()

    def chat(self, query: str, retriever: Any = None, llm: Any = None,
             include_history: bool = True, memory_key: str = "chat_history", 
             content: Optional[str] = None, 
             use_question_reformulation: bool = True) -> str:
        
        if llm is None:
            raise ValueError("An LLM must be provided to chat")
        
        
        history_for_reformulation = self.get_formatted_messages() 

        reformulated_query = query
        if use_question_reformulation and history_for_reformulation: 
            contextualize_chain = self.create_contextualize_chain(llm)
            try:
                reformulated_query = contextualize_chain.invoke({
                    "input": query,
                    "chat_history": history_for_reformulation 
                })
                print(f"Original query: '{query}' --- Reformulated: '{reformulated_query}'")
            except Exception as e:
                print(f"Question reformulation failed: {e}. Using original query.")
                reformulated_query = query
        
        
        self.chat_history.append(HumanMessage(content=query))

        if content is None and retriever is None:
            raise ValueError("Either retriever or content must be provided")
        
       
        if include_history:
            template = f"""Answer the question based on the following context and chat history.
            
            Context: {{context}}
            
            Chat History:
            {{{memory_key}}}
            
            Question: {{question}}
            
            Answer:"""
        else:
            template = """Answer the question based on the following context:
            
            Context: {context}
            
            Question: {question}
            
            Answer:"""
        
 
        current_prompt = RAG.create_prompt(template)
        
 
        chain = RAG.create_chain(retriever=retriever, content=content, llm=llm, prompt=current_prompt)
        
  
        chain_input = {"question": reformulated_query}
        if include_history:
            chain_input[memory_key] = self.get_formatted_history_str()
        
        response_str = chain.invoke(chain_input) 
        
        self.chat_history.append(AIMessage(content=response_str))
        
        return response_str
    
    def get_chat_history(self) -> List[Union[AIMessage, HumanMessage]]:
        return self.chat_history
    
    def clear_chat_history(self) -> None:
        self.chat_history = []