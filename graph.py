# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "aiosqlite",
#     "langgraph",
#     "langgraph-checkpoint-sqlite",
#     "mcp[cli]",
# ]
# ///
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import os
import asyncio
import argparse

server_params = StdioServerParameters(
    command="uvx",
    args=["comfy-mcp-server"],
    env={
        "COMFY_URL": os.getenv("COMFY_URL"),
        "COMFY_URL_EXTERNAL": os.getenv("COMFY_URL_EXTERNAL"),
        "COMFY_WORKFLOW_JSON_FILE": os.getenv("COMFY_WORKFLOW_JSON_FILE"),
        "PROMPT_NODE_ID": os.getenv("PROMPT_NODE_ID"),
        "OUTPUT_NODE_ID": os.getenv("OUTPUT_NODE_ID"),
        "OUTPUT_MODE": "url",
        "OLLAMA_API_BASE": os.getenv("OLLAMA_API_BASE"),
        "PROMPT_LLM": os.getenv("PROMPT_LLM"),
        "PATH": os.getenv("PATH"),
    }
)


class State(TypedDict):
    topic: str
    prompt: str
    user_feedback: str
    image_url: str


async def run_tool(tool: str, args: dict) -> str:
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.call_tool(
                tool, arguments=args
            )


async def generate_prompt(state: State) -> State:
    topic = state["topic"]
    result = await run_tool("generate_prompt", {"topic": topic})
    # print(f"Tool: generate_prompt, Input: {topic}, Result: {result}")
    state["prompt"] = result.content[0].text
    return state


async def generate_image(state: State) -> State:
    prompt = state["prompt"]
    result = await run_tool("generate_image", {"prompt": prompt})
    # print(f"Tool: generate_image, Input: {prompt}, Result: {result}")
    state["image_url"] = result.content[0].text
    return state


def prompt_feedback(state: State) -> State:
    state["user_feedback"] = interrupt({
        "topic": state["topic"],
        "prompt": state["prompt"],
        "action": "Do you like this prompt? (y/n)"
    })
    return state


def process_feedback(state: State) -> str:
    user_feedback = state["user_feedback"]
    if len(user_feedback.strip()) == 0 or user_feedback.lower().strip()[0] == "y":
        return "generate_image"
    return "generate_prompt"


builder = StateGraph(State)
builder.add_node("generate_prompt", generate_prompt)
builder.add_node("prompt_feedback", prompt_feedback)
builder.add_node("generate_image", generate_image)
builder.add_edge(START, "generate_prompt")
builder.add_edge("generate_prompt", "prompt_feedback")
builder.add_conditional_edges("prompt_feedback", process_feedback)
builder.add_edge("generate_image", END)


async def main():
    parser = argparse.ArgumentParser(
        prog="Comfy UI LangGraph MCP",
        description="Simple script demonstrating MCP server from LangGraph Graph API with Human-in-the-Loop."
    )
    parser.add_argument("thread_id")
    parser.add_argument("--topic", default="A cat holding 'AIMUG' sign")
    parser.add_argument("--feedback")

    args = parser.parse_args()
    thread_id = args.thread_id
    topic = args.topic
    feedback = args.feedback
    print(f"{thread_id=}")

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    prompt = {"topic": topic}
    async with AsyncSqliteSaver.from_conn_string("checkpoints.sqlite") as saver:
        graph = builder.compile(checkpointer=saver)
        state = await graph.aget_state(config)
        next = state.next[0] if len(state.next) > 0 else None
        if next == "prompt_feedback" and feedback is not None:
            prompt = Command(resume=feedback)
        async for item in graph.astream(prompt, config):
            step = list(item.keys())[0]
            print(f"Step: {step}")
            if "__interrupt__" in item:
                value = item['__interrupt__'][0].value
                print(
                    f"Prompt: {value['prompt']}\n\nAction: {value['action']}")
            elif "generate_image" in item:
                value = item['generate_image']
                print(f"Image: {value['image_url']}")


if __name__ == "__main__":
    asyncio.run(main())
