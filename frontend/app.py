# frontend/app.py
import streamlit as st
import requests
import json

st.set_page_config(
    page_title="Fi App Client",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state variables
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "login_url" not in st.session_state:
    st.session_state.login_url = None
if "data_fetched" not in st.session_state:
    st.session_state.data_fetched = False
if "data_summary" not in st.session_state:
    st.session_state.data_summary = None

st.title("🤖 Fi App Client")
st.markdown("---")

# Backend base URL
API_BASE_URL = "http://127.0.0.1:8000/api/v1"

def authenticate():
    try:
        response = requests.get(f"{API_BASE_URL}/authenticate")
        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            if status == "login_required":
                st.session_state.login_url = data.get("login_url")
                st.success("Authentication link received! Please click the button below.")
            elif status == "success":
                st.session_state.authenticated = True
                st.success("Authentication successful! You can now fetch data.")
            else:
                st.error("Unexpected response status from backend.")
        else:
            st.error(f"Backend error: Status code {response.status_code}")
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to backend. Please ensure the backend server is running.")


def fetch_data():
    try:
        response = requests.get(f"{API_BASE_URL}/fetch-data")
        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            if status == "success":
                st.session_state.data_fetched = True
                st.session_state.data_summary = data.get("summary", {})
                st.success("Financial data fetched successfully!")
            elif status == "login_required":
                st.warning("Authentication required before fetching data. Please authenticate again.")
                st.session_state.authenticated = False
                st.session_state.login_url = data.get("login_url")
            else:
                st.error(f"Data fetch failed: {data.get('message', 'Unknown error')}")
        else:
            st.error(f"Error fetching data: Status code {response.status_code}")
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to backend to fetch data.")

def show_data_summary(summary):
    if not summary:
        st.info("No data summary available.")
        return
    st.subheader("Data Summary")
    total_tools = summary.get("total_tools", 0)
    successful = summary.get("successful", 0)
    failed = summary.get("failed", 0)
    st.write(f"**Total tools:** {total_tools}")
    st.write(f"**Successful fetches:** {successful}")
    st.write(f"**Failed fetches:** {failed}")
    st.write("**Tools Status:**")
    tools_status = summary.get("tools_status", {})
    for tool, status in tools_status.items():
        st.write(f"- {tool}: {status}")

# --- UI Logic based on Session State ---
if not st.session_state.authenticated:
    st.info("To get personalized financial advice, please authenticate yourself with the FI app.")
    if st.button("Authenticate"):
        authenticate()

    if st.session_state.login_url:
        st.markdown(f"[Go to FI App Login]({st.session_state.login_url})", unsafe_allow_html=True)
        st.warning(
            "After authenticating in the new window, click the button below to continue."
        )
        if st.button("I have authenticated"):
            st.session_state.authenticated = True
            st.rerun()

else:
    st.success("You are authenticated!")
    st.info("You can now fetch your financial data.")
    if not st.session_state.data_fetched:
        if st.button("Fetch All Financial Data"):
            fetch_data()
    else:
        show_data_summary(st.session_state.data_summary)
        # Optionally, add a button to download the JSON data file if backend supports it
        if st.button("Download Data JSON"):
            try:
                download_url = f"{API_BASE_URL}/download-data"
                # Fetching data for download
                download_response = requests.get(download_url)
                if download_response.status_code == 200:
                    file_content = download_response.content
                    st.download_button(
                        label="Download JSON",
                        data=file_content,
                        file_name="fi_mcp_data.json",
                        mime="application/json",
                    )
                else:
                    st.error("No data available for download or failed to fetch.")
            except Exception as e:
                st.error(f"Download error: {str(e)}")
