import streamlit as st
import subprocess
import sys

st.set_page_config(page_title="AI Agent", page_icon="🤖")

st.title("AI Agent")

query = st.text_input("Ask your question")

if st.button("Submit"):

    if query.strip():

        try:
            process = subprocess.Popen(
                [sys.executable, "agent.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            output, error = process.communicate(
                input=query + "\nexit\n"
            )

            if error:
                st.error(error)
            else:
                st.text_area(
                    "Agent Output",
                    output,
                    height=400
                )

        except Exception as e:
            st.error(str(e))