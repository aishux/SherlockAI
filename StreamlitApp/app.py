import streamlit as st
import json
import base64
from generate_sketch import generate_forensic_sketch
from streamlit_lottie import st_lottie
from io import BytesIO
from generate_video import generate_crime_video
from graph_analysis import decision_maker

# Streamlit UI
st.set_page_config(layout="wide")
st.title("🕵️ Sherlock AI - Criminal Intelligence Platform")

tabs = st.sidebar.radio("Select Use Case", ["🧠 Query Criminal Graph", "✏️ Generate Sketch", "🎬 Enactment Video"])

if tabs == "🧠 Query Criminal Graph":
    col1, col2, col3 = st.columns([1, 2, 1])

    with col3:
        st.header("🔍 Internal Reasoning")
        reasoning_placeholder = st.empty()

    with col1:
        st.header("📂 Chat Input")
        user_query = st.text_area("Ask a question about the criminal graph", height=200)
        if "right_panel" not in st.session_state:
            st.session_state.right_panel = []

        if st.button("Submit", use_container_width=True):
            st.session_state.chat_response = "."
            reasoning_placeholder.empty()
            st.session_state.chat_response = decision_maker(user_query, reasoning_placeholder)

    with col2:
        st.header("🗨️ Natural Language Response")
        if "chat_response" in st.session_state:
            st.markdown(st.session_state.chat_response)

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

            st_lottie(lottie_sketch, speed=1, width=300, height=300, key="sketch_anim")

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
