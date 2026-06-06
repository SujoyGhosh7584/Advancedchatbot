import streamlit as st
from ai_engine import ChatBotEngine  # Import our backend controller

# Web browser tab and window metadata configuration
st.set_page_config(page_title="AI Chatbot", page_icon="🤖")
st.title("⚡ Modular High-Speed Chatbot")

# 🛠️ 1. INITIALIZE BACKEND ENGINE & STATE
if "bot_engine" not in st.session_state:
    # Customize your bot's core identity prompt string here
    st.session_state.bot_engine = ChatBotEngine(
        system_prompt="You are Jarvis, a brilliant and slightly sarcastic AI assistant."
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

# 🎨 2. SIDEBAR INTERACTION CONTROL
with st.sidebar:
    st.header("⚙️ Settings")
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# 💬 3. RENDER CONVERSATION HISTORY
for message in st.session_state.messages:
    avatar = "🧑‍💻" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# 🚀 4. HANDLE INCOMING USER INPUT
if prompt := st.chat_input("What is on your mind?"):
    # Append and render user text entry
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Pull streaming tokens dynamically from our backend generator block
    with st.chat_message("assistant", avatar="🤖"):
        try:
            stream_generator = st.session_state.bot_engine.get_streaming_response(
                st.session_state.messages
            )
            # Display text elements continuously on screen
            response = st.write_stream(stream_generator)
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"System Connection Error: {e}")
