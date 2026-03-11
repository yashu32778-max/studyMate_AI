import streamlit as st
from rag_pipeline import process_pdf, ask_question
from gtts import gTTS
from streamlit_agraph import agraph, Node, Edge, Config
from quiz_generator import generate_quiz
from translator import translate_text, text_to_audio
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph
import io

# -------------------------------------------------------
# Page Config - Must be at the very top
# -------------------------------------------------------
st.set_page_config(page_title="StudyMate AI", layout="wide", initial_sidebar_state="expanded")

# -------------------------------------------------------
# Custom CSS for Modern "NotebookLM" Dark Theme
# -------------------------------------------------------
st.markdown("""
<style>
    .main-title {
        font-size: 40px; text-align: center; color: #4CAF50;
        font-weight: bold; margin-bottom: 10px;
    }
    .section-header {
        font-size: 24px; color: #FFFFFF; font-weight: bold;
        margin-bottom: 15px; border-left: 5px solid #4CAF50; padding-left: 10px;
    }
    .stButton>button {
        background-color: #4CAF50; color: white; border-radius: 20px;
        width: 100%; border: none; height: 40px; font-weight: bold;
    }
    .stChatInputContainer { padding-bottom: 30px; }
    /* Make the Mind Map container look like a canvas */
    .css-1r6slb0 { background-color: #1e1e1e; border-radius: 15px; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Sidebar: Document Management
# -------------------------------------------------------
with st.sidebar:
    st.header("📂 Document Center")
    uploaded_files = st.file_uploader("Upload Study Material (PDF)", type=["pdf"], accept_multiple_files=True)
    
    if uploaded_files:
        for file in uploaded_files:
            with open(file.name, "wb") as f:
                f.write(file.read())
            process_pdf(file.name)
        st.success("Documents Processed!")
    
    st.divider()
    st.info("Tip: Use the Mind Map to visualize connections and the Chat to dive deeper.")

# -------------------------------------------------------
# TOP SECTION: Full-Width Mind Map (NotebookLM Style)
# -------------------------------------------------------
st.markdown('<p class="main-title">📚 StudyMate AI</p>', unsafe_allow_html=True)

st.markdown('<div class="section-header">🧠 Interactive Knowledge Map</div>', unsafe_allow_html=True)

# Generate Mind Map Logic
if st.button("✨ Generate / Refresh Knowledge Map"):
    # We ask the AI for a structured list to build the nodes
    mindmap_data = ask_question("Identify the 10 most important entities or concepts from this document. Return them as a simple bulleted list.")
    
    nodes, edges = [], []
    # Central Node
    nodes.append(Node(id="Center", label="Core Concept", size=30, color="#4CAF50", shape="diamond"))
    
    lines = mindmap_data.split("\n")
    for line in lines:
        clean_text = line.strip("- *• ").strip()
        if clean_text and len(clean_text) > 1:
            # Topic Nodes
            nodes.append(Node(id=clean_text, label=clean_text, size=20, color="#00bcd4"))
            # Connections
            edges.append(Edge(source="Center", target=clean_text, color="#555555"))

    # Config for FULL SCREEN view
    config = Config(
        width=1400, # Large width for full-screen feel
        height=500, 
        physics=True, # Allows nodes to float/bounce
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#F7A01B",
        collapsible=True
    )
    
    agraph(nodes=nodes, edges=edges, config=config)
else:
    st.info("Click 'Generate' to visualize your document as an interactive map.")

st.divider()

# -------------------------------------------------------
# BOTTOM SECTION: Divided into Tools and Chat
# -------------------------------------------------------
col_tools, col_chat = st.columns([1, 1.2], gap="large")

# LEFT SIDE: Study Tools
with col_tools:
    # Podcast
    st.markdown('<div class="section-header">🎙 Podcast Generator</div>', unsafe_allow_html=True)
    if st.button("Generate Audio Summary"):
        podcast_script = ask_question("Create a 1-minute engaging podcast script about this document.")
        st.write(podcast_script)
        tts = gTTS(podcast_script)
        tts.save("summary.mp3")
        st.audio("summary.mp3")

    # -------------------------------------------------------
    # Interactive Practice Quiz
    # -------------------------------------------------------
    st.markdown('<div class="section-header">📝 Practice Quiz</div>', unsafe_allow_html=True)

    if st.button("Generate Quiz from Document"):
        # IMPORTANT: Ensure 'last_answer' or 'full_text' is passed here
        context_to_use = st.session_state.get("last_answer", "")
        
        if not context_to_use:
            st.warning("Please ask a question about the document first to provide context!")
        else:
            with st.spinner("Creating questions..."):
                raw_quiz = generate_quiz(context_to_use)
                # Split the raw text into individual question blocks
                st.session_state.quiz_blocks = [q.strip() for q in raw_quiz.split("---") if "Question:" in q]

    # Display the interactive quiz
    if "quiz_blocks" in st.session_state:
        for i, block in enumerate(st.session_state.quiz_blocks):
            lines = block.split("\n")
            
            # Extract Question, Options, and the Correct Answer
            q_text = next((l for l in lines if "Question:" in l), "Question")
            opts = [l.strip() for l in lines if l.strip().startswith(('A)', 'B)', 'C)', 'D)'))]
            ans_line = next((l for l in lines if "Correct:" in l), "Correct: A")
            correct_ans = ans_line.split(":")[-1].strip()

            st.write(f"**{q_text}**")
            # Radio buttons for user selection
            user_choice = st.radio(f"Select your answer for Q{i+1}:", opts, key=f"radio_{i}")

            if st.button(f"Check Question {i+1}", key=f"check_{i}"):
                # Check if the chosen option starts with the correct letter
                if user_choice.startswith(correct_ans):
                    st.success(f"Correct! 🎯 The answer is {correct_ans}")
                else:
                    st.error(f"Incorrect. The correct answer was {correct_ans}")
            st.divider()
    # Translation
    st.markdown('<div class="section-header">🌍 Translator</div>', unsafe_allow_html=True)
    langs = {"Tamil":"ta", "Hindi":"hi", "French":"fr", "Spanish":"es"}
    target_lang = st.selectbox("Translate to:", list(langs.keys()))
    if st.button("Translate Last Response"):
        if "last_answer" in st.session_state:
            translated = translate_text(st.session_state.last_answer, langs[target_lang])
            st.success(translated)
        else:
            st.warning("Ask a question in the chat first!")

# RIGHT SIDE: Deep Chat
with col_chat:
    st.markdown('<div class="section-header">💬 Chat with Documents</div>', unsafe_allow_html=True)
    
    # Message History Container
    if "messages" not in st.session_state:
        st.session_state.messages = []

    chat_box = st.container(height=450)
    with chat_box:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    # Chat Input
    user_query = st.chat_input("Ask about the document...")
    if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query})
        with chat_box:
            st.chat_message("user").write(user_query)
        
        # Get AI Response
        ai_response = ask_question(user_query)
        st.session_state.last_answer = ai_response
        
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
        with chat_box:
            st.chat_message("assistant").write(ai_response)
        st.rerun()