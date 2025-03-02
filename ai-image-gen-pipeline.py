from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
import os
from langgraph.types import interrupt, Command
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    topic: str
    prompt: str
    user_feedback: str
    image_url: str


class Pipeline:
    class Valves(BaseModel):
        COMFY_URL: str
        COMFY_URL_EXTERNAL: str
        COMFY_WORKFLOW_JSON_FILE: str
        PROMPT_NODE_ID: str
        OUTPUT_NODE_ID: str
        OLLAMA_API_BASE: str
        PROMPT_LLM: str
        pass

    def __init__(self):
        self.name = "Comfy MCP Langgraph HIL Pipeline"
        self.valves = self.Valves(
            **{
                "COMFY_URL": os.getenv("COMFY_URL", "comfy-url"),
                "COMFY_URL_EXTERNAL": os.getenv("COMFY_URL_EXTERNAL",
                                                "comfy-url-external"),
                "COMFY_WORKFLOW_JSON_FILE": os.getenv(
                    "COMFY_WORKFLOW_JSON_FILE",
                    "path-to-workflow-json-file"),
                "PROMPT_NODE_ID": os.getenv("PROMPT_NODE_ID",
                                            "prompt-node-id"),
                "OUTPUT_NODE_ID": os.getenv("OUTPUT_NODE_ID",
                                            "output-node-id"),
                "OLLAMA_API_BASE": os.getenv("OLLAMA_API_BASE", "ollama-api-base"),
                "PROMPT_LLM": os.getenv("PROMPT_LLM", "prompt-llm")
            }
        )
        pass

    async def on_startup(self):
        print(f"on_startup:{__name__}")
        self.server_params = StdioServerParameters(
            command="uvx",
            args=["comfy-mcp-server"],
            env={
                "COMFY_URL": self.valves.COMFY_URL,
                "COMFY_URL_EXTERNAL": self.valves.COMFY_URL_EXTERNAL,
                "COMFY_WORKFLOW_JSON_FILE": self.valves.COMFY_WORKFLOW_JSON_FILE,
                "PROMPT_NODE_ID": self.valves.PROMPT_NODE_ID,
                "OUTPUT_NODE_ID": self.valves.OUTPUT_NODE_ID,
                "OUTPUT_MODE": "url",
                "OLLAMA_API_BASE": self.valves.OLLAMA_API_BASE,
                "PROMPT_LLM": self.valves.PROMPT_LLM,
                "PATH": os.getenv("PATH"),
            }
        )
        builder = StateGraph(State)
        builder.add_node("generate_prompt", self.generate_prompt)
        builder.add_node("prompt_feedback", self.prompt_feedback)
        builder.add_node("generate_image", self.generate_image)
        builder.add_edge(START, "generate_prompt")
        builder.add_edge("generate_prompt", "prompt_feedback")
        builder.add_conditional_edges("prompt_feedback", self.process_feedback)
        builder.add_edge("generate_image", END)
        self.builder = builder
        pass

    async def on_shutdown(self):
        print(f"on_shutdown:{__name__}")
        pass

    async def on_valves_updated(self):
        pass

    async def inlet(self, body: dict, user: dict) -> dict:
        print(f"inlet:{__name__}")

        print(body)
        print(user)

        return body

    async def outlet(self, body: dict, user: dict) -> dict:
        print(f"outlet:{__name__}")

        messages = body["messages"]
        last_message = messages[-1]
        if (last_message["role"] == "assistant"
                and last_message["content"][:5] == "data:"):
            image_url = last_message["content"]
            content = messages[-2]["content"]
            last_message["content"] = f"Generated: {content}"
            last_message["files"] = [{"type": "image", "url": image_url}]
            messages[-1] = last_message
            body["messages"] = messages

        return body

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        print(f"pipe:{__name__}")

        if body.get("title", False):
            return user_message

        thread_id = body.get("id")
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        async def apipe() -> str:
            async with AsyncSqliteSaver.from_conn_string("checkpoints.sqlite") as saver:
                graph = self.builder.compile(checkpointer=saver)
                state = await graph.aget_state(config)
                next = state.next[0] if len(state.next) > 0 else None
                response = "Invalid input"

                prompt = {"topic": user_message}
                if next == "prompt_feedback":
                    prompt = Command(resume=user_message)
                async for item in graph.astream(prompt, config):
                    step = list(item.keys())[0]
                    print(f"Step: {step}")
                    if "__interrupt__" in item:
                        value = item['__interrupt__'][0].value
                        print(
                            f"Prompt: {value['prompt']}\n\nAction: {value['action']}")
                        response = f"Prompt: {value['prompt']}\n\nAction: {value['action']}"
                    elif "generate_image" in item:
                        value = item['generate_image']
                        print(f"Image: {value['image_url']}")
                        image_url = value['image_url']
                        if image_url[:4] == 'http' and image_url[-11:] == 'type=output':
                            response = f"\n![image]({image_url})\n"
                        else:
                            response = image_url

                return response

        coro = apipe()
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            print("asyncio.run")
            result = asyncio.run(coro)
        else:
            print("loop.run_until_complete")
            result = loop.run_until_complete(coro)

        return result

    async def run_tool(self, tool: str, args: dict) -> str:
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await session.call_tool(
                    tool, arguments=args
                )

    async def generate_prompt(self, state: State) -> State:
        topic = state["topic"]
        result = await self.run_tool("generate_prompt", {"topic": topic})
        # print(f"Tool: generate_prompt, Input: {topic}, Result: {result}")
        state["prompt"] = result.content[0].text
        return state

    async def generate_image(self, state: State) -> State:
        prompt = state["prompt"]
        result = await self.run_tool("generate_image", {"prompt": prompt})
        # print(f"Tool: generate_image, Input: {prompt}, Result: {result}")
        state["image_url"] = result.content[0].text
        return state

    def prompt_feedback(self, state: State) -> State:
        state["user_feedback"] = interrupt({
            "topic": state["topic"],
            "prompt": state["prompt"],
            "action": "Do you like this prompt? (y/n)"
        })
        return state

    def process_feedback(self, state: State) -> str:
        user_feedback = state["user_feedback"]
        if len(user_feedback.strip()) == 0 or user_feedback.lower().strip()[0] == "y":
            return "generate_image"
        return "generate_prompt"
