import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List

# Page configuration
st.set_page_config(
    page_title="Asset Copilot - Industrial Asset AI Assistant",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .query-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .insight-box {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .error-box {
        background-color: #ffe6e6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff4444;
    }
    .success-box {
        background-color: #e6ffe6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #00aa00;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"  # Your FastAPI server

def check_api_health():
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def query_api(query: str) -> Dict:
    """Send query to the API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/query",
            json={"query": query},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None

def analyze_anomaly(equipment_id: str, anomaly_type: str) -> Dict:
    """Send anomaly analysis request to API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/analyze_anomaly",
            json={
                "equipment_id": equipment_id,
                "anomaly_type": anomaly_type,
                "severity": "WARNING"
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None

def create_severity_chart(logs: List[Dict]):
    """Create a chart showing severity distribution"""
    if not logs:
        return None
    
    df = pd.DataFrame(logs)
    severity_counts = df['severity'].value_counts()
    
    fig = px.pie(
        values=severity_counts.values,
        names=severity_counts.index,
        title="Log Severity Distribution",
        color_discrete_map={
            'INFO': '#00aa00',
            'WARNING': '#ffaa00', 
            'ERROR': '#ff4444'
        }
    )
    return fig

def create_timeline_chart(logs: List[Dict]):
    """Create a timeline of equipment events"""
    if not logs:
        return None
    
    df = pd.DataFrame(logs)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    fig = go.Figure()
    
    colors = {'INFO': '#00aa00', 'WARNING': '#ffaa00', 'ERROR': '#ff4444'}
    
    for severity in df['severity'].unique():
        severity_data = df[df['severity'] == severity]
        fig.add_trace(go.Scatter(
            x=severity_data['timestamp'],
            y=severity_data['equipment_id'],
            mode='markers',
            name=severity,
            marker=dict(color=colors.get(severity, '#1f77b4'), size=10),
            text=severity_data['message'],
            hovertemplate='<b>%{y}</b><br>%{x}<br>%{text}<extra></extra>'
        ))
    
    fig.update_layout(
        title="Equipment Events Timeline",
        xaxis_title="Time",
        yaxis_title="Equipment ID",
        height=400
    )
    return fig

# Main app
def main():
    # Header
    st.markdown('<h1 class="main-header">Asset Copilot - Industrial Asset AI Assistant</h1>', unsafe_allow_html=True)
    
    # Check API status
    api_status = check_api_health()
    
    if not api_status:
        st.markdown("""
        <div class="error-box">
        ⚠️ <strong>API Not Running</strong><br>
        Please start your FastAPI server first:<br>
        <code>uvicorn main:app --reload</code>
        </div>
        """, unsafe_allow_html=True)
        st.stop()
    else:
        st.markdown("""
        <div class="success-box">
        ✅ <strong>API Connected</strong> - Ready to analyze equipment data
        </div>
        """, unsafe_allow_html=True)
    
    # Sidebar for quick actions
    with st.sidebar:
        st.header("🔧 Quick Actions")
        
        st.subheader("Common Queries")
        quick_queries = [
            "Which pumps have issues?",
            "Recent temperature problems",
            "Equipment errors today",
            "Bearing maintenance needed",
            "High vibration alerts",
            "Pressure drop incidents"
        ]
        
        for query in quick_queries:
            if st.button(query, key=f"quick_{query}"):
                st.session_state.current_query = query
        
        st.subheader("Equipment Types")
        equipment_types = ["pump", "motor", "compressor", "turbine", "heat_exchanger"]
        selected_equipment = st.selectbox("Filter by equipment:", ["All"] + equipment_types)
        
        st.subheader("Severity Levels")
        severity_filter = st.multiselect(
            "Show severity:",
            ["INFO", "WARNING", "ERROR"],
            default=["WARNING", "ERROR"]
        )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 Ask the AI Assistant")
        
        # Query input
        query_input = st.text_input(
            "Enter your question about equipment:",
            value=st.session_state.get('current_query', ''),
            placeholder="e.g., 'What's wrong with pump_01?' or 'Recent bearing issues'"
        )
        
        col_query, col_anomaly = st.columns(2)
        
        with col_query:
            query_button = st.button("🔍 Analyze Equipment", type="primary")
        
        with col_anomaly:
            with st.expander("🚨 Report Anomaly"):
                equipment_id = st.text_input("Equipment ID:", placeholder="pump_01")
                anomaly_type = st.selectbox(
                    "Anomaly Type:",
                    ["temperature_spike", "vibration", "pressure_drop", "bearing_wear", "oil_leak"]
                )
                anomaly_button = st.button("Report Anomaly")
        
        # Process queries
        result = None
        
        if query_button and query_input:
            with st.spinner("🤖 AI is analyzing your query..."):
                result = query_api(query_input)
        
        elif anomaly_button and equipment_id and anomaly_type:
            with st.spinner("🤖 AI is analyzing the anomaly..."):
                result = analyze_anomaly(equipment_id, anomaly_type)
        
        # Display results
        if result:
            st.subheader("🎯 AI Analysis Results")
            
            # Show the insight
            st.markdown(f"""
            <div class="insight-box">
            <strong>🧠 AI Insight:</strong><br>
            {result['insight']}
            </div>
            """, unsafe_allow_html=True)
            
            # Show relevant logs
            if result['relevant_logs']:
                st.subheader("📋 Relevant Equipment Logs")
                
                # Create DataFrame for better display
                logs_df = pd.DataFrame(result['relevant_logs'])
                
                # Display as a nice table
                display_columns = ['timestamp', 'equipment_id', 'severity', 'message', 'facility']
                if all(col in logs_df.columns for col in display_columns):
                    logs_df['timestamp'] = pd.to_datetime(logs_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
                    
                    # Color code by severity
                    def highlight_severity(row):
                        if row['severity'] == 'ERROR':
                            return ['background-color: #ffe6e6'] * len(row)
                        elif row['severity'] == 'WARNING':
                            return ['background-color: #fff4e6'] * len(row)
                        else:
                            return [''] * len(row)
                    
                    styled_df = logs_df[display_columns].style.apply(highlight_severity, axis=1)
                    st.dataframe(styled_df, use_container_width=True)
                
                # Charts
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    severity_chart = create_severity_chart(result['relevant_logs'])
                    if severity_chart:
                        st.plotly_chart(severity_chart, use_container_width=True)
                
                with col_chart2:
                    timeline_chart = create_timeline_chart(result['relevant_logs'])
                    if timeline_chart:
                        st.plotly_chart(timeline_chart, use_container_width=True)
            
            else:
                st.info("No relevant logs found for your query.")
    
    with col2:
        st.header("📊 System Status")
        
        # API health metrics
        st.metric("API Status", "🟢 Online" if api_status else "🔴 Offline")
        st.metric("Last Query", datetime.now().strftime("%H:%M:%S"))
        
        # Example queries section
        st.subheader("💡 Example Queries")
        examples = [
            "What equipment needs immediate attention?",
            "Show me all temperature alerts",
            "Which motors are overheating?",
            "Recent pump maintenance issues",
            "Critical errors in Plant_A",
            "Equipment with bearing problems"
        ]
        
        for example in examples:
            if st.button(f"Try: {example}", key=f"example_{example}"):
                st.session_state.current_query = example
                st.rerun()
        
        # Help section
        with st.expander("❓ How to Use"):
            st.markdown("""
            **Query Types:**
            - Equipment-specific: "pump_01 issues"
            - Problem-type: "temperature problems"
            - Facility-based: "Plant_A errors"
            - Time-based: "recent alerts"
            
            **Features:**
            - Natural language queries
            - Real-time AI analysis
            - Visual data charts
            - Anomaly reporting
            """)

if __name__ == "__main__":
    # Initialize session state
    if 'current_query' not in st.session_state:
        st.session_state.current_query = ""
    
    main()