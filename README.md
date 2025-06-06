# AI Image Generation Pipeline with LangGraph and MCP

This project demonstrates the use of the Model Context Protocol (MCP) with LangGraph to create workflows that generate prompts and AI-generated images based on a given topic. The project consists of three main files: `app.py`, `graph.py`, and `ai-image-gen-pipeline.py`. Each file showcases different aspects of using MCP with LangGraph, including the [LangGraph Functional API](https://langchain-ai.github.io/langgraph/reference/func/), [Graph API](https://langchain-ai.github.io/langgraph/), and integration within [Open WebUI Pipelines](https://docs.openwebui.com/pipelines/). These scripts utilize the [Comfy MCP Server](https://pypi.org/project/comfy-mcp-server/) to generate AI image prompts and AI images.

## Files

### app.py

This script demonstrates the use of the LangGraph Functional API along with Human-in-the-Loop (HIL) interaction to generate prompts and AI-generated images based on a given topic. The workflow includes user feedback to approve generated prompts before generating the corresponding image.

#### Key Components:
- **Dependencies**: `aiosqlite`, `langgraph`, `langgraph-checkpoint-sqlite`, `mcp[cli]`.
- **Functions**:
  - `run_tool(tool: str, args: dict) -> str`: Runs a tool using the MCP server.
  - `generate_prompt(topic: str) -> str`: Generates a prompt for a given topic.
  - `generate_image(prompt: str) -> str`: Generates an image based on a given prompt.
  - `get_feedback(topic: str, prompt: str) -> str`: Collects user feedback on the generated prompt.
  - `workflow_func(saver)`: Defines the workflow function with checkpointing.
- **Main Function**: 
  - Parses command-line arguments to get thread id and optionally the topic and feedback.
  - Initializes the workflow and runs it, based on the provided input.

### graph.py

This script demonstrates the use of the LangGraph Graph API along with Human-in-the-Loop (HIL) interaction to generate prompts and AI-generated images based on a given topic. The workflow includes user feedback to approve generated prompts before generating the corresponding image.

#### Key Components:
- **Dependencies**: `aiosqlite`, `langgraph`, `langgraph-checkpoint-sqlite`, `mcp[cli]`.
- **Functions**:
  - `run_tool(tool: str, args: dict) -> str`: Runs a tool using the MCP server.
  - `generate_prompt(state: State) -> State`: Generates a prompt for a given topic and updates the state.
  - `generate_image(state: State) -> State`: Generates an image based on a given prompt and updates the state.
  - `prompt_feedback(state: State) -> State`: Collects user feedback on the generated prompt.
  - `process_feedback(state: State) -> str`: Processes the user feedback to determine the next step in the workflow.
- **Main Function**: 
  - Parses command-line arguments to get the thread ID, topic, and feedback.
  - Initializes the state graph and runs it based on the provided input.

### ai-image-gen-pipeline.py

This script demonstrates the integration of LangGraph API with Human-in-the-Loop (HIL) within [Open WebUI Pipelines](https://docs.openwebui.com/pipelines/). It defines a pipeline for generating prompts and images using MCP, including nodes for generating prompts, processing feedback, and generating images.

#### Key Components:
- **Dependencies**: `aiosqlite`, `langgraph`, `langgraph-checkpoint-sqlite`, `mcp[cli]`.
- **Classes**:
  - `Pipeline`: Defines the pipeline with nodes for generating prompts, processing feedback, and generating images.
    - `Valves(BaseModel)`: Contains environment variables for MCP server configuration.
- **Functions**:
  - `inlet(body: dict, user: dict) -> dict`: Processes incoming messages.
  - `outlet(body: dict, user: dict) -> dict`: Processes outgoing messages.
  - `pipe(user_message: str, model_id: str, messages: List[dict], body: dict) -> Union[str, Generator, Iterator]`: Defines the main pipeline logic.
  - `run_tool(tool: str, args: dict) -> str`: Runs a tool using the MCP server.
  - `generate_prompt(state: State) -> State`: Generates a prompt for a given topic and updates the state.
  - `generate_image(state: State) -> State`: Generates an image based on a given prompt and updates the state.
  - `prompt_feedback(state: State) -> State`: Collects user feedback on the generated prompt.
  - `process_feedback(state: State) -> str`: Processes the user feedback to determine the next step in the workflow.

## Usage

1. **Install Dependencies**: Ensure you have the required dependencies installed.
   ```bash
   pip install aiosqlite langgraph langgraph-checkpoint-sqlite mcp[cli] comfy-mcp-server
   ```

2. **Run the Application**:
   - For `app.py`:
     ```bash
     python app.py --topic "Your topic here"
     ```
   - For `graph.py`:
     ```bash
     python graph.py --thread_id "your-thread-id" --topic "Your topic here" 
     ```

     For feedback:
     ```bash
     python graph.py --thread_id "your-thread-id" --feedback "y/n" 
     ```

3. **Using `uv` Utility**: You can also launch `app.py` and `graph.py` using the [uv](https://docs.astral.sh/uv/) utility. This utility manages Python version and dependency management, so there is no need to preinstall dependencies.
   - For `app.py`:
     ```bash
     uv run app.py --topic "Your topic here"
     ```
   - For `graph.py`:
     ```bash
     uv run graph.py --thread_id "your-thread-id" --topic "Your topic here" 
     ```

     For feedback:
     ```bash
     uv run graph.py --thread_id "your-thread-id" --feedback "y/n" 
     ```

4. **Environment Variables**: Set the necessary environment variables for the OPENAI API key.
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```
   or .env file:
   ```
   OPENAI_API_KEY=your-openai-api-key
   ```


## Contributing

Feel free to contribute to this project by submitting pull requests or issues. Ensure that any changes are well-documented and tested.

## License

This project is licensed under the MIT License.
