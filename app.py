# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "aiosqlite",
#     "langgraph",
#     "langgraph-checkpoint-sqlite",
#     "mcp[cli]",
# ]
# ///
import uuid

from langgraph.func import entrypoint, task
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


async def run_tool(tool: str, args: dict) -> str:
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.call_tool(
                tool, arguments=args
            )


@task
async def generate_prompt(topic: str) -> str:
    result = await run_tool("generate_prompt", {"topic": topic})
    # print(f"Tool: generate_prompt, Input: {topic}, Result: {result}")
    return result.content[0].text


@task
async def generate_image(prompt: str) -> str:
    result = await run_tool("generate_image", {"prompt": prompt})
    # print(f"Tool: generate_image, Input: {prompt}, Result: {result}")
    return result.content[0].text


def workflow_func(saver):
    @entrypoint(checkpointer=saver)
    async def workflow(topic: str) -> dict:
        """A simple workflow that generates prompts and an ai generated image for a topic."""

        is_approved = "n"
        while is_approved.lower()[0] != "y":
            prompt = await generate_prompt(topic)
            is_approved = interrupt({
                "topic": topic,
                "prompt": prompt,
                "action": "Do you like this prompt (y/n)?",
            })

        image_url = await generate_image(prompt)
        return {
            "topic": topic,
            "prompt": prompt,
            "image_url": image_url
        }
    return workflow


async def main():
    parser = argparse.ArgumentParser(
        prog="Comfy UI LangGraph MCP",
        description="Simple script demonstrating MCP server from LangGraph Functional API with Human-in-the-Loop."
    )
    parser.add_argument("--topic", default="A cat holding 'AIMUG' sign")

    args = parser.parse_args()
    topic = args.topic
    thread_id = str(uuid.uuid4())

    print(f"{thread_id=}")

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    prompt = topic
    async with AsyncSqliteSaver.from_conn_string("checkpoints.sqlite") as saver:
        workflow = workflow_func(saver)
        stop = False
        while not stop:
            async for item in workflow.astream(prompt, config):
                step = list(item.keys())[0]
                print(f"Step: {step}")
                if "workflow" in item:
                    # print(item)
                    image_url = item['workflow']['image_url']
                    print(f"Image URL: {image_url}")
                    stop = True
                    break
                # continue
                if "__interrupt__" in item:
                    # print(item)
                    value = item['__interrupt__'][0].value
                    print(f"Prompt: {value['prompt']}")
                    hil_input = input(
                        f"{value['action']}: ")
                    if len(hil_input.strip()) == 0:
                        hil_input = "y"
                    prompt = Command(resume=hil_input)
                else:
                    pass


if __name__ == "__main__":
    asyncio.run(main())
