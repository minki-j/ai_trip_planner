from langchain_community.tools import TavilySearchResults

from app.state import OverallState, InputState, OutputState
from app.llm import chat_model


def tavily_search(state: OverallState):
    print("\n>>> NODE: tavily_search")

    tavily = TavilySearchResults(
        max_results=5,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=True,
        include_images=False,
        # include_domains=[...],
        # exclude_domains=[...],
        # name="...",            # overwrite default tool name
        # description="...",     # overwrite default tool description
        # args_schema=...,       # overwrite default args_schema: BaseModel
    )

    for query in state.queries_for_internet_search:
        result = tavily.invoke(query)
        print("tavily_search result: ", result)


    return {""}