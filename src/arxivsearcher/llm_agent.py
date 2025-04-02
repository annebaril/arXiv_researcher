import os
from langchain.agents import AgentExecutor, create_structured_chat_agent
from dotenv import load_dotenv

load_dotenv()

def create_agent(llm, tools, prompt):
    agent = create_structured_chat_agent(llm, tools, prompt)

    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        verbose=os.getenv("VERBOSE"),  # Use the conversation memory to maintain context
        handle_parsing_errors=True,  # Handle any parsing errors gracefully
    )
    return agent_executor