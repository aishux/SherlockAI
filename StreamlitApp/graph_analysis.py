import networkx as nx
import nest_asyncio
import ssl
import certifi
import re
import pickle
from langchain_openai import AzureChatOpenAI
from GremlinGraph import GremlinGraph
from langchain_core.prompts import ChatPromptTemplate

# Load the NetworkX graph
with open("graph.pkl", "rb") as f:
    G = pickle.load(f)

# Required for async execution in notebooks and Streamlit
nest_asyncio.apply()
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Cosmos DB Config
COSMOS_DB_ENDPOINT = 'wss://sherlock-ai-account.gremlin.cosmos.azure.com:443/'
COSMOS_DB_PRIMARY_KEY = 'cjLqpPhvEE5F9pLrIG82jZ4ie87UVsJVs1XRJAV1lmxIri5VyQ3uS4tgX505AlouYjDqfeAYGkZBACDbf3PkJw=='
DATABASE = 'sherlock-db'
GRAPH = 'sherlock-ai-graph'

graph = GremlinGraph(
    url=COSMOS_DB_ENDPOINT,
    username=f"/dbs/{DATABASE}/colls/{GRAPH}",
    password=COSMOS_DB_PRIMARY_KEY,
    ssl_context=ssl_context
)

# Azure OpenAI Config
AZURE_OPENAI_ENDPOINT = "https://aishu-m8q3ed4m-swedencentral.cognitiveservices.azure.com/"
AZURE_OPENAI_KEY = "028qDuTdd4Z5y0nsdbVns8ZesZeQxt4NEQmW33BObOs7cLO9gIteJQQJ99BCACfhMk5XJ3w3AAAAACOGWE1L"
AZURE_DEPLOYMENT_NAME = "gpt-4o"

llm = AzureChatOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    openai_api_version="2025-01-01-preview",
    azure_deployment=AZURE_DEPLOYMENT_NAME,
    api_key=AZURE_OPENAI_KEY,
    temperature=0
)

gremlin_msg = """
This is a Chicago Crime Network stored in Azure Cosmos DB Gremlin Graph, with the following node and edge labels:
crime node is connected to all the other nodes by the edges mentioned.
All other nodes are having a inbound connection from crime
Vertex labels are the following: crime,location,crime_type,criminal,district,date,hour Edge labes are the following: located_at,is_type,occurred_at_hour,occurred_on_date,involved_criminal,located_in_district Vertices have following properties: ["crime":["crime_id"],"location":["location"],"crime_type":["crime_type"],"criminal":["name"],"district":["district"],"date":["date"],"hour":["hour"]]'
If asked to find information about given node ids then GENERATE A SINGLE QUERY to fetch all.
DO NOT use elementMap() in your queries instead use valueMap().
ONLY GIVE ME THE GREMLIN QUERY. DO NOT PROVIDE ANY INSTRUCTIONS.
"""

gremlin_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            gremlin_msg
        ),
        ("human", "{input}"),
    ]
)

gremlin_chain = gremlin_prompt | llm


networkx_msg = """
** THERE SHOULD BE NO TEXT IN THE OUTPUT, JUST CODE **
1. ONLY provide python code that I can directly execute via `exec()`. Do not provide any instructions.
2. Code must reference `G` as the networkx graph.
3. Use only `networkx (nx)`. nx is already available so no need to import.
4. Store the final result in `FINAL_RESULT`.
5. Use the correct algorithm

Python Code:
"""

networkx_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            networkx_msg
        ),
        ("human", "{input}"),
    ]
)

networkx_chain = networkx_prompt | llm

decision_msg = """
You are a Criminal Tracking & Analysis Agent using Cosmos Gremlin and NetworkX.
Generate python code based on the user query below understanding which method you need to call and what query is to be passed.
Use hybrid queries where required. For example: To find shortest path between two criminals first call the text_to_nxgraph method 
to get the node ids involved in shortest path which returns node ids no need to extract anything and then get information about these IDs using gremlin method text_to_gremlin with a single query mentioning that these are node ids. Always the last step is to craft and send the prompt to llm.invoke() method to generate a well crafted summary. In the prompt include all the results that we go till now. For paths join them with arrows properly and accurately including all nodes.
Methods available:
- text_to_gremlin (STRICTLY only receives natural language queries then Generates and Executes Gremlin queries in Consmos DB.)
- text_to_nxgraph (Executes python code for networkx graph analysis. Result is returned from this method so no need to execute)
ONLY GIVE ME THE PYTHON CODE. DO NOT PROVIDE ANY INSTRUCTIONS.
"""

decision_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            decision_msg
        ),
        ("human", "{input}"),
    ]
)

decision_chain = decision_prompt | llm

curr_reasoning_placeholder = ""
reasoning_log = []

# Helper functions
def text_to_gremlin(query: str) -> str:
    global curr_reasoning_placeholder,reasoning_log
    gremlin_query = gremlin_chain.invoke({"input": query}).content
    gremlin_query = gremlin_query.split("\n")[1]
    reasoning_log.append(f"🟢 **Gremlin Query:**\n```groovy\n{gremlin_query}\n```")
    curr_reasoning_placeholder.markdown("\n\n".join(reasoning_log))
    return graph.query(gremlin_query)

def text_to_nxgraph(query: str) -> str:
    global curr_reasoning_placeholder,reasoning_log
    graph_analysis_code = networkx_chain.invoke({"input": query}).content
    cleaned_code = re.sub(r"^```python\n|```$", "", graph_analysis_code, flags=re.MULTILINE).strip()
    reasoning_log.append(f"🟡 **NetworkX Code:**\n```python\n{cleaned_code}\n```")
    curr_reasoning_placeholder.markdown("\n\n".join(reasoning_log))
    global_vars = {"G": G, "nx": nx}
    local_vars = {}
    try:
        exec(cleaned_code, global_vars, local_vars)
        return local_vars.get("FINAL_RESULT", "No result found.")
    except Exception as e:
        return f"Error executing networkx code: {e}"

def decision_maker(query: str, reasoning_placeholder):
    global curr_reasoning_placeholder,reasoning_log
    reasoning_log = []
    decision_code = decision_chain.invoke({"input": query}).content
    cleaned = re.sub(r"^```python\n|```$", "", decision_code, flags=re.MULTILINE).strip()
    curr_reasoning_placeholder = reasoning_placeholder
    reasoning_log.append(f"🔵 **Decision Code:**\n```python\n{cleaned}\n```")
    curr_reasoning_placeholder.markdown("".join(reasoning_log))

    global_vars = {
        "G": G, "nx": nx,
        "text_to_gremlin": text_to_gremlin,
        "text_to_nxgraph": text_to_nxgraph,
        "llm": llm,
        "curr_reasoning_placeholder": curr_reasoning_placeholder,
        "reasoning_log": reasoning_log
    }
    local_vars = {}
    try:
        exec(cleaned, global_vars, local_vars)
        return local_vars.get("summary", "No result found.").content
    except Exception as e:
        return f"Error executing decision code: {e}"