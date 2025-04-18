import os
from langchain.agents import AgentExecutor, create_structured_chat_agent
from dotenv import load_dotenv
from arxivsearcher.retrieval import create_search_tool
from arxivsearcher.chroma_qa import create_semantic_tool
from langchain.memory import ConversationBufferMemory

load_dotenv()

def create_agent(vectorstore, llm, prompt):
    search_articles_tool = create_search_tool(vectorstore)
    semantic_tool = create_semantic_tool(llm, vectorstore)

    tools = [search_articles_tool, semantic_tool]
    agent = create_structured_chat_agent(llm=llm, tools=tools, prompt=prompt)
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=os.getenv("VERBOSE"),  # Use the conversation memory to maintain context
        handle_parsing_errors=True,
        return_intermediate_steps=True  # Handle any parsing errors gracefully
    )
    return agent_executor