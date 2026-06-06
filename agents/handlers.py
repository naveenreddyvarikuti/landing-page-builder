import os
from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from tools.file_tools import read_file, list_files, search_codebase

load_dotenv()

_llm = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)

_question_agent = create_react_agent(
    _llm,
    tools=[search_codebase, read_file, list_files],
    prompt="You answer questions about a landing page. Use search_codebase to find relevant code by concept or feature name, then read_file to inspect full file contents if needed. Give clear, specific answers based only on what's in the files.",
)


def run_question(question: str) -> str:
    result = _question_agent.invoke({"messages": [{"role": "user", "content": question}]})
    return result["messages"][-1].content


def run_copy(question: str) -> str:
    response = _llm.invoke([
        {"role": "system", "content": "You are a copywriter for a landing page. Write compelling, concise copy based on the request. Return only the copy text, no explanation."},
        {"role": "user", "content": question},
    ])
    return response.content
