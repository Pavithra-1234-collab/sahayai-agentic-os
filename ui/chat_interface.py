import streamlit as st
from agents.orchestrator import process_message

SUGGESTED_PROMPTS = [
    ("📦", "Check Inventory", "Show me products with low stock"),
    ("💰", "Price Analysis", "Give me pricing advice for my products"),
    ("📝", "Create Listing", "Create an Amazon listing for Bluetooth Speaker"),
    ("📊", "Weekly Report", "Show me my sales report for the last 7 days"),
    ("⭐", "Review Summary", "Summarise my customer reviews"),
    ("📈", "Growth Insights", "How is my business performing this month?"),
]


def render_chat():
    st.title("💬 AI Business Manager Chat")
    st.caption("Ask anything about your Amazon & Flipkart business")

    # Initialise session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "history" not in st.session_state:
        st.session_state.history = []

    # Suggested prompts (only shown when chat is empty)
    if not st.session_state.messages:
        st.markdown("**Quick actions:**")
        cols = st.columns(3)
        for i, (icon, label, prompt) in enumerate(SUGGESTED_PROMPTS):
            with cols[i % 3]:
                if st.button(f"{icon} {label}", use_container_width=True, key=f"suggested_{i}"):
                    st.session_state["pending_prompt"] = prompt
                    st.rerun()

        st.markdown("---")
        # Welcome message
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(
                "Namaste! 🙏 I'm your AI Business Manager. I can help you manage your "
                "**Amazon.in** and **Flipkart** stores.\n\n"
                "Ask me to check stock, analyse prices, write listings, or show sales reports. "
                "What would you like to do today?"
            )

    # Render conversation history
    for msg in st.session_state.messages:
        avatar = "🧑‍💼" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # Handle pending prompt from quick-action buttons
    if "pending_prompt" in st.session_state:
        user_input = st.session_state.pop("pending_prompt")
        _handle_message(user_input)
        st.rerun()

    # Chat input
    if prompt := st.chat_input("Ask me anything about your business..."):
        _handle_message(prompt)
        st.rerun()

    # Clear chat button
    if st.session_state.messages:
        if st.button("🗑️ Clear chat", key="clear_chat"):
            st.session_state.messages = []
            st.session_state.history = []
            st.rerun()


def _handle_message(user_input: str):
    # Add user message to display
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Show thinking indicator and get response
    with st.chat_message("user", avatar="🧑‍💼"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            response = process_message(user_input, st.session_state.history)
        st.markdown(response)

    # Update history for multi-turn memory
    st.session_state.history.append({"role": "user", "content": user_input})
    st.session_state.history.append({"role": "assistant", "content": response})

    # Add assistant message to display
    st.session_state.messages.append({"role": "assistant", "content": response})
