

import os
import uuid
from google.adk.agents.llm_agent import Agent
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.sequential_agent import SequentialAgent
#from google.adk.agents import Agent
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai.preview import rag
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from sqlalchemy import create_engine, text
from google.adk.tools import function_tool


from dotenv import load_dotenv
from .prompts import return_instructions_root

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



rag_agent = Agent(
    model='gemini-2.5-flash',
    name='ask_rag_agent',
    instruction=return_instructions_root(),
    tools= tools,
    output_key= "rag_response"
)
    


web_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='Consolidate resp',
    instruction='You are a helpful agent that will take response from rag agent {rag_response} and search the web for more information if needed before answering the user. Please provide a final comprehensive response to the user query with proper citation and web links to the resources.',
    output_key= "final_response"
) 



# Setup a simple database connection (e.g., SQLite for this example)
# In production, replace this with your Cloud SQL or Postgres connection string
""" engine = create_engine("sqlite:///my_database.db")

def query_database(sql_query: str) -> str:
    """
    Executes a SQL query against the company database and returns the results.
    
    Args:
        sql_query: The SQL syntax to execute (e.g., "SELECT * FROM orders LIMIT 5")
        
    Returns:
        A string representation of the query results.
    """
    try:
        # Safety check: purely for example. In production, use read-only users!
        if "DROP" in sql_query.upper() or "DELETE" in sql_query.upper():
            return "Error: Destructive actions are not allowed."
            
        with engine.connect() as connection:
            print(sql_query)
            result = connection.execute(text(sql_query))
            rows = result.fetchall()
            return str(rows)
    except Exception as e:
        return f"Database error: {str(e)}"


# Create the agent with the database tool
db_agent = Agent( """
    name="sql_analyst",
    model="gemini-2.5-flash",  # Or your preferred model
    description="An expert data analyst helper.",
    instruction="""
    You are a helpful data analyst. Your goal is to answer user questions by querying the database.
    1. Translate the user's natural language question into a valid SQL query.
    2. Use the 'query_database' tool to execute the query.
    3. Interpret the results and answer the user's question in plain English.
    """,
    tools=[query_database] # <--- Register your tool here
)

consolidate_agent = SequentialAgent(
    name="consolidateagent",
    sub_agents=[rag_agent, web_agent],
    description="An agent that first retrieves relevant documents using RAG and then consolidates the information to answer the user's query.",
)

# For ADK tools compatibility, the root agent must be named `root_agent`
root_agent = consolidate_agent

session_service = InMemorySessionService()

# Step 3: Create the Runner
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)




