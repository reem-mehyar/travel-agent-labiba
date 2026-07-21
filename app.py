"""
Streamlit frontend for Labiba AI Travel Agent.

This file ONLY renders the UI and talks to the existing TravelAgent class.
No backend logic is duplicated or modified here.
"""

import streamlit as st

from travel_agent import TravelAgent


# ==================================================
# Page Configuration
# ==================================================

st.set_page_config(
    page_title="Labiba AI Travel Agent",
    page_icon="🌍",
    layout="centered",
    initial_sidebar_state="expanded",
)


# ==================================================
# Dark Mode Styling
# ==================================================

def inject_custom_css() -> None:
    """
    Inject custom CSS for a modern dark-mode chat interface.
    """

    st.markdown(
        """
        <style>
        /* App background */
        .stApp {
            background-color: #0e1117;
            color: #e6e6e6;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #14151c;
            border-right: 1px solid #262730;
        }

        /* Title spacing */
        .main-title {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0rem;
        }

        .main-subtitle {
            color: #9ca3af;
            font-size: 1rem;
            margin-top: 0.2rem;
            margin-bottom: 1.5rem;
        }

        /* Chat message bubbles */
        div[data-testid="stChatMessage"] {
            border-radius: 14px;
            padding: 0.75rem 1rem;
            margin-bottom: 0.6rem;
        }

        /* Reset button */
        div.stButton > button {
            width: 100%;
            border-radius: 10px;
            border: 1px solid #3a3b46;
            background-color: #1c1d26;
            color: #e6e6e6;
        }

        div.stButton > button:hover {
            border-color: #6366f1;
            color: #6366f1;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ==================================================
# Session State Initialization
# ==================================================

def initialize_session_state() -> None:
    """
    Create the TravelAgent instance and chat history ONCE per session.
    The agent must never be recreated on every message.
    """

    if "agent" not in st.session_state:
        st.session_state.agent = TravelAgent()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


def reset_conversation() -> None:
    """
    Recreate the TravelAgent and clear the chat history.
    """

    st.session_state.agent = TravelAgent()
    st.session_state.chat_history = []


# ==================================================
# Sidebar
# ==================================================

def render_sidebar() -> None:
    """
    Render the sidebar with app branding, supported features,
    and the reset conversation button.
    """

    with st.sidebar:
        st.markdown("## 🌍 Labiba AI Travel Agent")
        st.markdown("---")

        st.markdown("### Supported Features")
        st.markdown(
            """
            ✓ Hotel Search
            ✓ Flight Search
            ✓ Weather Forecast
            ✓ Currency Conversion
            ✓ Conversation Memory
            """
        )

        st.markdown("---")

        if st.button("🔄 Reset Conversation"):
            reset_conversation()
            st.rerun()


# ==================================================
# Header
# ==================================================

def render_header() -> None:
    """
    Render the main page title and subtitle.
    """

    st.markdown(
        '<div class="main-title">🌍 Labiba AI Travel Agent</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="main-subtitle">'
        "Plan your trips with hotels, flights, weather, and currency conversion."
        "</div>",
        unsafe_allow_html=True,
    )


# ==================================================
# Chat History Rendering
# ==================================================

def render_chat_history() -> None:
    """
    Render all previous messages from the chat history.
    """

    for message in st.session_state.chat_history:
        role = message["role"]
        content = message["content"]

        with st.chat_message(role):
            st.markdown(content)


# ==================================================
# Handling New User Messages
# ==================================================

def handle_user_message(user_message: str) -> None:
    """
    Send the user's message to the TravelAgent, display the
    assistant's response, and update the chat history.

    Args:
        user_message:
            The message typed by the user.
    """

    # Store and display the user message.
    st.session_state.chat_history.append(
        {"role": "user", "content": user_message}
    )

    with st.chat_message("user"):
        st.markdown(user_message)

    # Get the assistant's response.
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.agent.handle_request(user_message)

        st.markdown(response)

    # Store the assistant response.
    st.session_state.chat_history.append(
        {"role": "assistant", "content": response}
    )


# ==================================================
# Main Application
# ==================================================

def main() -> None:
    """
    Entry point for the Streamlit application.
    """

    inject_custom_css()
    initialize_session_state()

    render_sidebar()
    render_header()

    render_chat_history()

    user_message = st.chat_input("Ask me about hotels, flights, weather, or currency...")

    if user_message:
        handle_user_message(user_message)


if __name__ == "__main__":
    main()
