"""
GenBI POC - Phase 1: Data Asset Discovery Assistant

Intelligent data asset query application based on DBT metadata
Uses LangChain Agent to automatically discover and query data assets
"""

import streamlit as st
import os
from agents.agent import ask_agent

# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="GenBI POC - Phase 1",
    page_icon="🔍",
    layout="wide"
)

# ============================================================================
# Page Title
# ============================================================================

st.title("🔍 Data Asset Discovery Assistant")
st.caption("Intelligent Query Based on DBT Metadata")

# ============================================================================
# Check Environment Configuration
# ============================================================================

# Check if OPENAI_API_KEY is set
if not os.getenv("OPENAI_API_KEY"):
    st.error("⚠️ OPENAI_API_KEY is not set. Please configure the API key in your .env file.")
    st.stop()

# ============================================================================
# Initialize Session State
# ============================================================================

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

    # Add welcome message
    welcome_message = """👋 Hello! I'm your Data Asset Discovery Assistant.

I can help you:
- Find tables and models in your DBT project
- Understand table field structures and meanings
- Explore data assets

Try asking me a question, or click on the examples in the sidebar!"""

    st.session_state.messages.append({
        "role": "assistant",
        "content": welcome_message
    })

# ============================================================================
# Sidebar - Example Questions and Features
# ============================================================================

with st.sidebar:
    st.header("💡 Try These Questions")

    # Example questions list
    example_questions = [
        "What tables do we have?",
        "Are there any order-related tables?",
        "Describe the structure of the dim_customers table in detail",
        "Which tables contain customer information?",
        "Tell me about tables related to sales data",
        "List all dimension tables"
    ]

    # Create button for each example
    for question in example_questions:
        if st.button(question, key=f"example_{question}", use_container_width=True):
            # Process example question as user input
            # Add user message
            st.session_state.messages.append({
                "role": "user",
                "content": question
            })

            # Call Agent to get response
            with st.spinner("🤔 Thinking..."):
                try:
                    response = ask_agent(question)

                    # Add assistant response
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response
                    })
                except Exception as e:
                    # Error handling
                    error_message = f"Sorry, an error occurred while processing your question: {str(e)}"
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_message
                    })

            # Refresh page to display new messages
            st.rerun()

    # Divider
    st.sidebar.divider()

    # Clear conversation button
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        # Clear message history
        st.session_state.messages = []

        # Re-add welcome message
        welcome_message = """👋 Hello! I'm your Data Asset Discovery Assistant.

I can help you:
- Find tables and models in your DBT project
- Understand table field structures and meanings
- Explore data assets

Try asking me a question, or click on the examples in the sidebar!"""

        st.session_state.messages.append({
            "role": "assistant",
            "content": welcome_message
        })

        # Refresh page
        st.rerun()

    # About section
    st.sidebar.divider()
    st.sidebar.markdown("### About")
    st.sidebar.info("""
    **GenBI POC - Phase 1**

    Technologies Used:
    - DBT (Data Build Tool)
    - LangChain & LangGraph
    - OpenAI GPT-4o-mini
    - MCP (Model Context Protocol)
    - Streamlit

    Features: Intelligent data asset discovery and querying
    """)

# ============================================================================
# Display Chat History
# ============================================================================

# Iterate and display all messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ============================================================================
# User Input Processing
# ============================================================================

# Chat input box
if prompt := st.chat_input("Ask me about data tables..."):
    # Add user message to history
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call Agent to get response
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            try:
                # Call Agent
                response = ask_agent(prompt)

                # Display response
                st.markdown(response)

                # Add assistant response to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response
                })

            except Exception as e:
                # Error handling
                error_message = f"""Sorry, an error occurred while processing your question.

**Error message:** {str(e)}

Please ensure:
1. DBT MCP Server is running
2. OPENAI_API_KEY is configured correctly
3. Network connection is stable

You can try:
- Rephrase your question
- Click on example questions in the sidebar
- Clear the conversation and try again
"""

                st.error(error_message)

                # Add error message to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message
                })

# ============================================================================
# Footer
# ============================================================================

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Powered by DBT + LangChain + OpenAI | GenBI POC Phase 1"
    "</div>",
    unsafe_allow_html=True
)
