import asyncio
from dotenv import load_dotenv
from mirascope import llm, prompt_template
from mirascope.core import Messages
from mirascope.mcp import sse_client

load_dotenv()


@llm.call(provider="openai", model="gpt-4.1-mini")
@prompt_template("""
SYSTEM: You are a helpful research assistant. You are given a paper ID and you need to summarize the paper.
Use the ReadPaper tool to read the paper, and then summarize it.

USER: Please summarize the following paper:\n{paper_content}                 
""")
def summarize_paper(paper_content: str):
    """Summarize a paper from arXiv given it's paper ID"""
    ...


@llm.call(provider="openai", model="gpt-4.1-mini")
@prompt_template("""
SYSTEM: You are a helpful research assistant.
You use arxiv search tools to search for papers to answer the user's question.
You always write your findings in a structured format to a github gist when you are done.

You should follow the following process:
1. Execute Arxiv Search Tool to find relevant papers
2. For each paper, use the ReadPaper tool to read the paper
3. Summarize each paper using the Summarize Paper Tool
4. Create a github gist with the summary of the research

Remember: you MUST create a github gist.

<report_format>
# [[Title]]

[[Short Description of Research Question]]

## Summary of Work
                 
[[Summary of papers found]]

## Papers
                 
[[List of Papers]]
</report_format>

USER: {query}

MESSAGES: {history}  
""")
async def mini_research(query: str, *, history: list[Messages.Type] | None = None): ...

async def _try_tool_call(tool):
    try:
        return await tool.call()
    except Exception as e:
        return "Error calling {tool._name()}: {e}"
        

async def _process_tools(resp):
    """process the tool calls.
    
    When the LLM requests tools, there may be multiple. For efficiency we run them
    asynchronously. This likely makes sense because we are communicating over a network
    for these tool calls! 
    """
    if tools := resp.tools:
        for t in tools: print('Calling', t._name()) # noqa: E701
        tasks = [_try_tool_call(t) for t in tools]
        tool_results = await asyncio.gather(*tasks)
        return list(zip(tools, tool_results))
    return None



async def _one_step(query: str, tools, history: list[Messages.Type] | None = None):
    """A single step for the agent.
    
    The core step for an agent is get a response from the core llm which may contain tools.
    If there are tools, we call and process them.
    """
    tools = [t for t in tools if 'Download' not in t._name()]
    resp = await llm.override(mini_research, tools=tools + [summarize_paper])(query, history=history)
    history.append(resp.message_param)
    tool_calls = await _process_tools(resp)
    if tool_calls:
        history += resp.tool_message_params(tool_calls)
    # We are only 'done' if no more tool calls
    return resp, history, len(tool_calls or []) == 0


async def run(query: str, *, tools, max_steps: int = 10):
    """Main agent loop.
    
    An 'agent' is really just a loop where you continually interleave LLM calls and tool calls until some
    stop criteria is met. That could be too many steps, llm says it is done, or some other external heuristic even!
    A key part of this is that we keep track of history.
    """
    done = False
    history = []
    i = 0
    while not done and i < max_steps:
        resp, history, done = await _one_step(query, tools=tools, history=history)
    if not done:
        raise ValueError(f'Max steps {max_steps} reached!')
    return resp


async def main():
    async with sse_client("http://localhost:8000/sse") as client:
        tools = await client.list_tools()
        for t in tools:
            print(t._name(), t._description())
        
        query = input("\n\nEnter a research query: ")
        resp = await run(query, tools=tools)
        print(resp)


if __name__ == "__main__":
    asyncio.run(main())