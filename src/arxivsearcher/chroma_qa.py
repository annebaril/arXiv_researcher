from langchain_core.tools import tool
from langchain.chains import RetrievalQA


def create_semantic_tool(llm, vectorstore):

    @tool
    def semantic_search(title):
        """Use the knowledge of the arxiv dataset to answer questions, input: 'Show me some researches about Large Language Model', output: 'abstracts of articles about LLM"""
        retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 10})
        qa_chain = RetrievalQA.from_chain_type(llm, retriever=retriever)
        response = qa_chain.invoke(title)
        return response['result']
    
    return semantic_search