import streamlit as st


with st.form("Task"):
   st.write("LLM linear optimizer")
   task = st.text_area("Problem Formulation in natural language:")
   st.form_submit_button("Solve")

st.write(task)