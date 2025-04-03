import os
from langchain.agents import AgentExecutor, create_structured_chat_agent
from dotenv import load_dotenv
from arxivsearcher.retrieval import create_search_tool
from arxivsearcher.chroma_qa import semantic_search


load_dotenv()

def create_agent(vectorstore, llm, prompt):
    search_articles_tool = create_search_tool(vectorstore)
    tools = [search_articles_tool]
    agent = create_structured_chat_agent(llm, tools, prompt)

    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        verbose=os.getenv("VERBOSE"),  # Use the conversation memory to maintain context
        handle_parsing_errors=True,  # Handle any parsing errors gracefully
    )
    return agent_executor