import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from retriever import ask
import streamlit as st

st.set_page_config(page_title="Anime Discovery Assistant", page_icon="🎌")

st.title("🎌 Anime Discovery Assistant")
st.caption("Ask for recommendations in plain English — powered by RAG (LangChain + Gemini + ChromaDB)")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            st.caption("Sources: " + ", ".join(msg["sources"]))

query = st.chat_input("e.g. Something like Death Note but less dark")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Searching the anime database..."):
            result = ask(query)
        st.markdown(result["answer"])
        if result["sources"]:
            st.caption("Sources: " + ", ".join(result["sources"]))

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "sources": result["sources"]
    })
