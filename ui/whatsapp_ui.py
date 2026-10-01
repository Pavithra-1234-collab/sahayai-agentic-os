import streamlit as st
from datetime import datetime
from agents.orchestrator import process_message

WHATSAPP_SUGGESTIONS = [
    "Kitna stock bacha hai? (How much stock is left?)",
    "Show me this week's sales",
    "Create a listing for wireless earbuds",
    "Which products need reorder?",
    "Summarise my customer reviews",
    "What price should I set for the Bluetooth speaker?",
]

WHATSAPP_CSS = """
<style>
.wa-container {
    background: #0B141A;
    border-radius: 12px;
    padding: 0;
    overflow: hidden;
    max-width: 480px;
    margin: 0 auto;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
.wa-header {
    background: #1F2C34;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    gap: 12px;
    border-bottom: 1px solid #2A373F;
}
.wa-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: linear-gradient(135deg, #25D366, #128C7E);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    flex-shrink: 0;
}
.wa-contact-info .name {
    color: #E9EDEF;
    font-size: 16px;
    font-weight: 600;
}
.wa-contact-info .status {
    color: #25D366;
    font-size: 12px;
}
.wa-messages {
    background: #0B141A;
    background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.02'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
    padding: 16px 12px;
    min-height: 400px;
    max-height: 500px;
    overflow-y: auto;
}
.wa-bubble-user {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 6px;
}
.wa-bubble-user .bubble {
    background: #005C4B;
    color: #E9EDEF;
    border-radius: 12px 12px 2px 12px;
    padding: 8px 12px;
    max-width: 80%;
    font-size: 14px;
    line-height: 1.5;
    position: relative;
}
.wa-bubble-bot {
    display: flex;
    justify-content: flex-start;
    margin-bottom: 6px;
}
.wa-bubble-bot .bubble {
    background: #1F2C34;
    color: #E9EDEF;
    border-radius: 12px 12px 12px 2px;
    padding: 8px 12px;
    max-width: 80%;
    font-size: 14px;
    line-height: 1.5;
}
.wa-time {
    font-size: 11px;
    color: #8696A0;
    margin-top: 4px;
    text-align: right;
}
</style>
"""


def _format_whatsapp(text: str) -> str:
    """Convert WhatsApp-style markdown to HTML."""
    import re
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.*?)\*', r'<strong>\1</strong>', text)
    text = re.sub(r'_(.*?)_', r'<em>\1</em>', text)
    text = text.replace('\n', '<br>')
    return text


def render_whatsapp():
    st.title("📱 WhatsApp Business Interface")
    st.caption("Experience how the AI manager works on WhatsApp — same brain, WhatsApp look & feel")

    # Initialise state
    if "wa_messages" not in st.session_state:
        st.session_state.wa_messages = []
    if "wa_history" not in st.session_state:
        st.session_state.wa_history = []

    st.markdown(WHATSAPP_CSS, unsafe_allow_html=True)

    # ── Suggested messages ─────────────────────────────────────────────
    st.markdown("**Try these messages:**")
    cols = st.columns(2)
    for i, suggestion in enumerate(WHATSAPP_SUGGESTIONS):
        with cols[i % 2]:
            if st.button(suggestion[:45] + ("..." if len(suggestion) > 45 else ""),
                         key=f"wa_sug_{i}", use_container_width=True):
                st.session_state["wa_pending"] = suggestion
                st.rerun()

    st.markdown("---")

    # ── WhatsApp Chrome ────────────────────────────────────────────────
    now = datetime.now().strftime("%I:%M %p")

    # Build messages HTML
    messages_html = ""
    for msg in st.session_state.wa_messages:
        ts = msg.get("time", now)
        if msg["role"] == "user":
            messages_html += f"""
            <div class="wa-bubble-user">
              <div class="bubble">
                {_format_whatsapp(msg['content'])}
                <div class="wa-time">{ts} ✓✓</div>
              </div>
            </div>"""
        else:
            messages_html += f"""
            <div class="wa-bubble-bot">
              <div class="bubble">
                {_format_whatsapp(msg['content'])}
                <div class="wa-time">{ts}</div>
              </div>
            </div>"""

    if not messages_html:
        messages_html = """
        <div class="wa-bubble-bot">
          <div class="bubble">
            🙏 Namaste! I'm your AI Business Manager.<br><br>
            Ask me about your <strong>stock, pricing, sales reports</strong> or say "create a listing for [product]".<br><br>
            You can type in English or <strong>Hinglish</strong>!
            <div class="wa-time">Just now</div>
          </div>
        </div>"""

    wa_html = f"""
    <div class="wa-container">
      <div class="wa-header">
        <div class="wa-avatar">🤖</div>
        <div class="wa-contact-info">
          <div class="name">AI Business Manager</div>
          <div class="status">● online</div>
        </div>
      </div>
      <div class="wa-messages" id="wa-scroll">
        {messages_html}
      </div>
    </div>
    <script>
      const el = document.getElementById('wa-scroll');
      if (el) el.scrollTop = el.scrollHeight;
    </script>
    """
    st.markdown(wa_html, unsafe_allow_html=True)

    # ── Input ─────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col_input, col_send = st.columns([5, 1])
    with col_input:
        user_input = st.text_input(
            "", placeholder="Type a message...",
            label_visibility="collapsed",
            key="wa_input",
        )
    with col_send:
        send = st.button("Send ➤", type="primary", use_container_width=True)

    # Handle pending (from suggestion buttons)
    if "wa_pending" in st.session_state:
        _handle_wa_message(st.session_state.pop("wa_pending"))
        st.rerun()

    if send and user_input:
        # Clear the input box before rerun to prevent double-send
        del st.session_state["wa_input"]
        _handle_wa_message(user_input)
        st.rerun()

    if st.button("🗑️ Clear conversation", key="wa_clear"):
        st.session_state.wa_messages = []
        st.session_state.wa_history = []
        st.rerun()


def _handle_wa_message(text: str):
    now = datetime.now().strftime("%I:%M %p")
    st.session_state.wa_messages.append({"role": "user", "content": text, "time": now})

    with st.spinner(""):
        response = process_message(text, st.session_state.wa_history)

    st.session_state.wa_messages.append({"role": "assistant", "content": response, "time": now})
    st.session_state.wa_history.append({"role": "user", "content": text})
    st.session_state.wa_history.append({"role": "assistant", "content": response})
