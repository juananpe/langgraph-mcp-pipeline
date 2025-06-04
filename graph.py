# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "aiosqlite",
#     "langgraph",
#     "langgraph-checkpoint-sqlite",
#     "mcp[cli]",
#     "openai",
#     "python-dotenv",
#     "requests",
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

# Updated server parameters for our DALL-E MCP server
server_params = StdioServerParameters(
    command="uv",
    args=["run", "main.py"],
    cwd=os.path.dirname(os.path.abspath(__file__)),
    env={
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
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
    """Generate an enhanced prompt for DALL-E based on the topic"""
    topic = state["topic"]
    
    # Enhanced prompt generation for better DALL-E results
    enhanced_prompts = {
        "cat": f"{topic}, highly detailed, photorealistic, professional photography, studio lighting",
        "robot": f"{topic}, futuristic design, sleek metallic surfaces, LED details, cinematic lighting",
        "landscape": f"{topic}, breathtaking vista, golden hour lighting, ultra-wide angle, 8K quality",
        "portrait": f"{topic}, professional portrait, soft natural lighting, shallow depth of field",
        "abstract": f"{topic}, abstract art style, vibrant colors, dynamic composition, modern art",
    }
    
    # Simple keyword matching or use the topic directly with enhancement
    enhanced_prompt = topic
    for keyword, template in enhanced_prompts.items():
        if keyword.lower() in topic.lower():
            enhanced_prompt = template
            break
    else:
        # Default enhancement if no keyword matches
        enhanced_prompt = f"{topic}, high quality, detailed, professional, artistic"
    
    state["prompt"] = enhanced_prompt
    return state


async def generate_image(state: State) -> State:
    """Generate image using DALL-E MCP server"""
    prompt = state["prompt"]
    result = await run_tool("generate_image", {
        "prompt": prompt,
        "model": "dall-e-3",
        "size": "1024x1024",
        "quality": "standard"
    })
    # The result should contain the file path and success message
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
        prog="DALL-E LangGraph MCP",
        description="Simple script demonstrating DALL-E MCP server from LangGraph Graph API with Human-in-the-Loop."
    )
    parser.add_argument("--thread_id")
    parser.add_argument("--topic", default="A cute robot holding a 'Hello World' sign")
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
                print(f"Generated: {value['image_url']}")


if __name__ == "__main__":
    asyncio.run(main())
