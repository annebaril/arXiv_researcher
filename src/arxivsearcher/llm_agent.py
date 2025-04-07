import os
from langchain.agents import AgentExecutor, create_structured_chat_agent
from dotenv import load_dotenv
from arxivsearcher.retrieval import create_search_tool
from arxivsearcher.chroma_qa import create_semantic_tool
from arxivsearcher.trend_analysis import create_trend_tool

load_dotenv()

def create_agent(vectorstore, llm, prompt):
    search_articles_tool = create_search_tool(vectorstore)
    semantic_tool = create_semantic_tool(llm, vectorstore)
    trend_tool = create_trend_tool(vectorstore)

    tools = [search_articles_tool, semantic_tool]
    agent = create_structured_chat_agent(llm=llm, tools=tools, prompt=prompt)

    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        verbose=os.getenv("VERBOSE"),  # Use the conversation memory to maintain context
        handle_parsing_errors=True,
        return_intermediate_steps=True  # Handle any parsing errors gracefully
    )
    return agent_executor