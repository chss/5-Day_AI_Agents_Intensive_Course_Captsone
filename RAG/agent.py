
import os
import uuid
#from google.adk.agents.llm_agent import Agent
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.agents import Agent
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai.preview import rag
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from sqlalchemy import create_engine, text
from google.adk.tools import function_tool
from toolbox_core import ToolboxSyncClient

# Initialize ToolboxSyncClient and load toolset
toolbox = ToolboxSyncClient("http://127.0.0.1:5001")
toolset = toolbox.load_toolset("my-toolset")



from dotenv import load_dotenv
try:
    from .prompts import return_instructions_root
except ImportError:
    from prompts import return_instructions_root

load_dotenv()

# Build tools list conditionally based on RAG_CORPUS availability
tools = []

APP_NAME = "ragagent"  # Application
USER_ID = "u101"  # User
SESSION = str(uuid.uuid4())  # Session


# Check for RAG_CORPUS environment variable
rag_corpus = os.environ.get("RAG_CORPUS")

# If RAG_CORPUS is set, add the VertexAiRagRetrieval tool
if rag_corpus:
    ask_vertex_retrieval = VertexAiRagRetrieval(
        name='retrieve_rag_documentation',
        description=(
            'Use this tool to retrieve documentation and reference materials for the question from the RAG corpus,'
        ),
        rag_resources=[
            rag.RagResource(
                rag_corpus=rag_corpus
            )
        ],
        similarity_top_k=10,
        vector_distance_threshold=0.6,
    )
    tools.append(ask_vertex_retrieval)


#rag agent to retrieve information from the RAG corpus
rag_agent = Agent(
    model='gemini-2.5-pro',
    name='ask_rag_agent',
    instruction=return_instructions_root(),
    tools= tools,
    output_key= "rag_response"
)
    

#web agent to search the web for information
web_agent = Agent(
    model='gemini-2.5-pro',
    name='web_search_agent',
    description='Search the web for information',
    instruction='You are a helpful agent that will search the web for information related to the user query. Provide the search results.',
    output_key="web_response"
)

#db agent to retrieve information from the big query database. 
# Pay attention to use of MCP server to retrieve information from the database
db_agent = Agent(
    model='gemini-2.5-pro',
    name='db_agent',
    description='A helpful assistant for user questions related to signia products.',
    instruction='Answer user questions to the best of your knowledge using tools as needed',
    output_key="db_response",
    tools=toolset,
)

#parallel agent to run multiple agents in parallel to gather information
parallel_agent = ParallelAgent(
    name="ParallelAgent",
    sub_agents=[rag_agent,web_agent,db_agent],
    description="Runs multiple agents in parallel to gather information."
)

#merger agent to merge the information from the parallel agents
merger_agent = LlmAgent(
    name="SynthesisAgent",
    model='gemini-2.5-pro',  # Or potentially a more powerful model if needed for synthesis
    instruction="""You are an AI Assistant responsible for combining findings into a structured report.

Your primary task is to synthesize the following  summaries, clearly attributing findings to their source areas. Structure your response using headings for each topic. Ensure the report is coherent and integrates the key points smoothly.

**Crucially: Your entire response MUST be grounded *exclusively* on the information provided in the 'Input Summaries' below. Do NOT add any external knowledge, facts, or details not present in these specific summaries.**

**Input Summaries:**

*   **Internal Documentation:**
    {rag_response}

*   **Web Search:**
    {web_response}

*   **Database:**
     {db_response}

**Output Format:**

## Summary of Recent Sustainable Technology Advancements

### Internal Documentation Findings
(Based on Internal Documentation findings)
[Synthesize and elaborate *only* on the Internal Documentation input summary provided above.]

### Web Search Findings
(Based on Web Search findings)
[Synthesize and elaborate *only* on the Web Search input summary provided above.]

### Database Findings
(Based on Database findings)
[Synthesize and elaborate *only* on the Database input summary provided above.]

### Overall Conclusion
[Provide a brief (1-2 sentence) concluding statement that connects *only* the findings presented above.]

Output *only* the structured report following this format. Do not include introductory or concluding phrases outside this structure, and strictly adhere to using only the provided input summary content.
""",
    description="Combines findings from parallel agents into a structured, cited report, strictly grounded on provided inputs.",
    # No tools needed for merging
    # No output_key needed here, as its direct response is the final output of the sequence
)


#sequential pipeline agent to run the parallel agent and merger agent in sequence
sequential_pipeline_agent = SequentialAgent(
    name="SequentialPipelineAgent",
    # Run parallel research first, then merge
    sub_agents=[parallel_agent, merger_agent],
    description="Coordinates parallel agents and synthesizes the results."
)
#root agent to run the sequential pipeline agent
root_agent = sequential_pipeline_agent

#session service to store the session
session_service = InMemorySessionService()

#runner to run the agent
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)




