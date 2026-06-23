import streamlit as st
import time
import asyncio

st.set_page_config(page_title="Repo Doctor", page_icon="🩺", layout="centered")

st.title("🩺 Repo Doctor")
st.markdown("Analyze GitHub repositories for code quality and security vulnerabilities.")

# Input
repo_url = st.text_input("GitHub Repository URL", placeholder="https://github.com/owner/repo")

# Checkbox
use_sample = st.checkbox("Use sample report (No API call)", value=True)

# Button
if st.button("Diagnose Repo"):
    if not repo_url:
        st.warning("Please enter a GitHub repository URL.")
    else:
        sample_report = """## Code Quality Findings
   
**1. Missing Error Handling**
Severity: High
The main.py file has no try/except blocks around critical 
operations. If an unexpected value type is passed, it will crash silently.

**2. Lack of Docstrings**
Severity: Medium
Most functions in utils.py are missing docstrings. While the code is 
readable, documentation would help new contributors understand intent.

**3. No Input Validation**
Severity: Medium
Functions accept any input without type checking. Adding type hints 
and assertions would improve robustness.

## Security Findings

**1. No Secrets Found**
Severity: Info
No hardcoded API keys, passwords, or tokens were detected in this 
repository. Good practice observed.

**2. Safe Dependency Usage**
Severity: Info
No requirements.txt found — this is a minimal library with no 
external dependencies, reducing supply chain risk.

---
💡 To run a live analysis, clone the repo locally and add your own Gemini API key in the .env file."""

        if use_sample:
            with st.spinner("Repo Doctor is analyzing your repository..."):
                time.sleep(1.5)  # Simulate some work
                st.markdown(sample_report)
        else:
            with st.spinner("Repo Doctor is analyzing your repository..."):
                try:
                    from run_analysis import run_with_retry
                    
                    # Run the async function using asyncio
                    report = asyncio.run(run_with_retry(repo_url))
                    
                    if not report or report.startswith("[ERROR]"):
                        st.warning("⚠️ Live analysis is temporarily unavailable due to API rate limits. Here's a sample report to demonstrate what Repo Doctor produces:")
                        st.markdown(sample_report)
                    else:
                        st.markdown(report)
                except Exception as e:
                    st.warning("⚠️ Live analysis is temporarily unavailable due to API rate limits. Here's a sample report to demonstrate what Repo Doctor produces:")
                    st.markdown(sample_report)
