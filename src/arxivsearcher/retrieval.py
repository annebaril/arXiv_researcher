from langchain_core.tools import tool
from langchain_chroma import Chroma

def create_search_tool(vectorstore: Chroma):
    
    @tool
    def search_articles(title, nb_articles=3, year=None):
        """look for the most relevant articles about the theme, in a specific year if it's given. input: "give me some articles on AI published after 2005", output: "article 1: title, authors, abstract, etc"."""
        retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": nb_articles})
        retriever_docs = retriever.invoke(title)
        return retriever_docs
    
    return search_articles
