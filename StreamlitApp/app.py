import streamlit as st
import networkx as nx
import nest_asyncio
import ssl
import certifi
import re
import json
import pickle
import base64
from langchain_openai import AzureChatOpenAI
from GremlinGraph import GremlinGraph
from langchain_core.prompts import ChatPromptTemplate
from generate_sketch import generate_forensic_sketch
from streamlit_lottie import st_lottie
from io import BytesIO
from generate_video import generate_crime_video
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
AVOID USING elementMap() in your 
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

# Helper functions
def text_to_gremlin(query: str) -> str:
    gremlin_query = gremlin_chain.invoke({"input": query}).content.split("\n")[1]
    st.session_state.right_panel.append(f"🟢 **Gremlin Query:**\n```groovy\n{gremlin_query}\n```")
    return graph.query(gremlin_query)

def text_to_nxgraph(query: str) -> str:
    graph_analysis_code = networkx_chain.invoke({"input": query}).content
    cleaned_code = re.sub(r"^```python\n|```$", "", graph_analysis_code, flags=re.MULTILINE).strip()
    st.session_state.right_panel.append(f"🟡 **NetworkX Code:**\n```python\n{cleaned_code}\n```")
    global_vars = {"G": G, "nx": nx}
    local_vars = {}
    try:
        exec(cleaned_code, global_vars, local_vars)
        return local_vars.get("FINAL_RESULT", "No result found.")
    except Exception as e:
        return f"Error executing networkx code: {e}"

def decision_maker(query: str):
    decision_code = decision_chain.invoke({"input": query}).content
    cleaned = re.sub(r"^```python\n|```$", "", decision_code, flags=re.MULTILINE).strip()
    st.session_state.right_panel.append(f"🔵 **Decision Code:**\n```python\n{cleaned}\n```")
    global_vars = {
        "G": G, "nx": nx,
        "text_to_gremlin": text_to_gremlin,
        "text_to_nxgraph": text_to_nxgraph,
        "llm": llm
    }
    local_vars = {}
    try:
        exec(cleaned, global_vars, local_vars)
        return local_vars.get("summary", "No result found.").content
    except Exception as e:
        return f"Error executing decision code: {e}"

# Streamlit UI
st.set_page_config(layout="wide")
st.title("🕵️ Sherlock AI - Criminal Intelligence Platform")

tabs = st.sidebar.radio("Select Use Case", ["🧠 Query Criminal Graph", "✏️ Generate Sketch", "🎬 Enactment Video"])

if tabs == "🧠 Query Criminal Graph":
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        st.header("📂 Chat Input")
        user_query = st.text_area("Ask a question about the criminal graph", height=200)
        if "right_panel" not in st.session_state:
            st.session_state.right_panel = []

        if st.button("Submit", use_container_width=True):
            st.session_state.chat_response = decision_maker(user_query)

    with col2:
        st.header("🗨️ Natural Language Response")
        if "chat_response" in st.session_state:
            st.markdown(st.session_state.chat_response)

    with col3:
        st.header("🔍 Internal Reasoning")
        for block in st.session_state.right_panel[::-1]:
            st.markdown(block)

# Placeholder for other tabs (to be implemented later)
elif tabs == "✏️ Generate Sketch":
    with st.form("sketch_form"):
        col1, col2 = st.columns(2)
        with col1:
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            age = st.text_input("Age", placeholder="e.g., 35")
            eye_color = st.selectbox("Eye Color", ["Black", "Brown", "Blue", "Green", "Hazel", "Grey"])
            hair_color = st.selectbox("Hair Color", ["Black", "Brown", "Blonde", "Red", "Grey", "White"])
            skin_tone = st.selectbox("Skin Tone", ["Fair", "Light", "Medium", "Olive", "Brown", "Dark"])

        with col2:
            extra_desc = st.text_area("Additional Facial Features", placeholder="e.g., sharp jawline, thin lips, slightly crooked nose, wearing a hoodie")

        submitted = st.form_submit_button("Generate Sketch")

    if submitted:
        with st.spinner("Generating sketch... please wait..."):
            
            with open("lottie-animation.json", "r") as f:
                lottie_sketch = json.load(f)

            with st_lottie(lottie_sketch, speed=1, width=300, height=300, key="sketch_anim"):

                user_query = f"is a {gender} who is {age} years old, {skin_tone.lower()} skin, {hair_color.lower()} hair, {eye_color.lower()} eyes"
                if extra_desc.strip():
                    user_query += f", {extra_desc.strip()}"

                sketch = generate_forensic_sketch(user_query)

                st.image(sketch, caption="👤 Forensic Sketch", width=500)

                # Download button
                buffered = BytesIO()
                sketch.save(buffered, format="PNG")
                b64_img = base64.b64encode(buffered.getvalue()).decode()
                href = f'<a href="data:image/png;base64,{b64_img}" download="forensic_sketch.png">📥 Download Sketch</a>'
                st.markdown(href, unsafe_allow_html=True)
elif tabs == "🎬 Enactment Video":
    st.title("Crime Scene Reenactment")

    # Input field for user crime scene description
    scene_description = st.text_area("Describe the crime scene", placeholder="Enter a detailed description of the crime scene...")

    # Placeholder for logs
    log_placeholder = st.empty()

    # Submit button
    if st.button("Generate Video"):
        if scene_description.strip():
            log_placeholder.info("🔍 Breaking down the scene...")

            # Call the video generation function and pass the logs placeholder for real-time updates
            video_blob = generate_crime_video(scene_description, log_placeholder)

            # Show success message and download button
            if video_blob:
                st.video(video_blob)
                log_placeholder.success("✅ Video ready! Download your video below.")
                st.download_button("📥 Download Crime Scene Video", video_blob, file_name="crime_scene_reenactment.mp4")
        else:
            st.warning("Please provide a description of the crime scene.")
