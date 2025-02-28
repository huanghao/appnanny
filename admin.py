import streamlit as st
import requests

# ========================================================================
# Streamlit UI in the same file
# Usage: streamlit run appnanny.py
# (This is not typical production practice, but shown as a demonstration)
# ========================================================================
st.title("AppNanny - Managed Applications")

st.markdown("""
**Note**: This is a demonstration of having both a Flask API and a Streamlit UI in one file.
In a real-world scenario, you might run them separately or have a more robust approach.
"""
)

backend_url = "http://localhost:5000"

if "apps_data" not in st.session_state:
    st.session_state["apps_data"] = {}

if st.button("Refresh App List"):
    try:
        resp = requests.get(f"{backend_url}/apps")
        st.session_state["apps_data"] = resp.json()
    except Exception as e:
        st.error(f"Error fetching apps: {e}")

if st.session_state["apps_data"]:
    for app_name, info in st.session_state["apps_data"].items():
        with st.container():
            st.subheader(f"App: {app_name}")
            st.write(f"Type: {info['type']}")
            st.write(f"Repo: {info['repo']}")
            st.write(f"Path: {info['path']}")
            st.write(f"Email: {info['email']}")
            st.write(f"Active: {info['is_active']}")
            st.write(f"Running: {info['running']}")
            if info['running']:
                st.write(f"Port: {info['port']}")
                st.write(f"Uptime (sec): {info['uptime']:.1f}")
            col1, col2, col3 = st.columns([1,1,1])
            if col1.button(f"Stop {app_name}"):
                try:
                    requests.post(f"{backend_url}/stop/{app_name}")
                    st.success(f"Sent stop signal to {app_name}")
                except Exception as e:
                    st.error(str(e))
            if col2.button(f"Restart {app_name}"):
                try:
                    requests.post(f"{backend_url}/restart/{app_name}")
                    st.success(f"Sent restart signal to {app_name}")
                except Exception as e:
                    st.error(str(e))
            st.write("---")
else:
    st.write("No apps loaded. Click 'Refresh App List' above.")

# Additional features like 'delete permanently', 'shutdown', 'set environment vars'
# would be implemented similarly with more endpoints.
