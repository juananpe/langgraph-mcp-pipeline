# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "aiosqlite",
#     "langgraph",
#     "langgraph-checkpoint-sqlite==2.0.6",
#     "mcp[cli]",
# ]
# ///
from langgraph.func import entrypoint, task
from langgraph.types import interrupt, Command
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import os
import asyncio
import argparse
import textwrap

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


@task
def get_feedback(topic: str, prompt: str) -> str:
    feedback = interrupt({
        "topic": topic,
        "prompt": prompt,
        "action": "Do you like this prompt (y/n)?",
    })
    return feedback


def workflow_func(saver):
    @entrypoint(checkpointer=saver)
    async def workflow(topic: str) -> dict:
        """A simple workflow that generates prompts and an ai generated image for a topic."""

        is_approved = "n"
        while is_approved.lower()[0] != "y":
            prompt = await generate_prompt(topic)
            is_approved = await get_feedback(topic, prompt)

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
    parser.add_argument("thread_id")
    parser.add_argument("--topic")
    parser.add_argument("--feedback")

    args = parser.parse_args()
    topic = args.topic
    thread_id = args.thread_id
    feedback = args.feedback

    print(f"{thread_id=}")

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    prompt = topic
    async with AsyncSqliteSaver.from_conn_string("checkpoints.sqlite") as saver:
        workflow = workflow_func(saver)
        state = await workflow.aget_state(config)

        if state.values is not None and state.values != {}:
            value = state.values
            print(textwrap.dedent(f"""\
            Topic: {value['topic']}
            Prompt: {value['prompt']}
            Image: {value['image_url']}
            """))
            return

        current_interrupt = state.tasks[0].interrupts[0].value if len(
            state.tasks) > 0 and len(state.tasks[0].interrupts) > 0 else None
        if current_interrupt is not None:
            value = current_interrupt
            print(textwrap.dedent(f"""\
            Topic: {value['topic']}
            Prompt: {value['prompt']}
            Action: {value['action']}
            """))
            if feedback is not None:
                prompt = Command(resume=feedback)
            else:
                return

        if prompt is not None:
            async for item in workflow.astream(prompt, config, stream_mode="updates"):
                step = list(item.keys())[0]
                print(f"Step: {step}")
                if "workflow" in item:
                    # print(item)
                    image_url = item['workflow']['image_url']
                    print(f"Image URL: {image_url}")
                if "__interrupt__" in item:
                    # print(item)
                    value = item['__interrupt__'][0].value
                    print(textwrap.dedent(f"""\
                    Prompt: {value['prompt']}
                    {value['action']}: 
                    """))


if __name__ == "__main__":
    asyncio.run(main())
