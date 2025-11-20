import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
import time
import json
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
st.set_page_config(
    page_title="AI Email Agent Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f77b4;
    }
    .status-running {
        border-left-color: #2ecc71;
    }
    .status-stopped {
        border-left-color: #e74c3c;
    }
    .status-warning {
        border-left-color: #f39c12;
    }
</style>
""", unsafe_allow_html=True)


class EmailAgentDashboard:
    """Main dashboard class for AI Email Agent."""

    def __init__(self, api_url: str = API_BASE_URL):
        self.api_url = api_url
        self.session = requests.Session()

    def api_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
        """Make API request with error handling."""
        try:
            url = f"{self.api_url}{endpoint}"

            if method == "GET":
                response = self.session.get(url, timeout=10)
            elif method == "POST":
                response = self.session.post(url, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")

            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"API Error: {response.status_code} - {response.text}")
                return {}

        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {str(e)}")
            return {}

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status from API."""
        return self.api_request("/health")

    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get monitoring status from API."""
        return self.api_request("/status")

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.api_request("/stats")

    def start_monitoring(self, interval_minutes: int = 5) -> bool:
        """Start email monitoring."""
        return bool(self.api_request(f"/monitoring/start?interval_minutes={interval_minutes}", "POST"))

    def stop_monitoring(self) -> bool:
        """Stop email monitoring."""
        return bool(self.api_request("/monitoring/stop", "POST"))

    def process_emails(self, limit: int = None, dry_run: bool = False) -> Dict[str, Any]:
        """Process emails manually."""
        data = {"dry_run": dry_run}
        if limit:
            data["limit"] = limit
        return self.api_request("/emails/process", "POST", data)

    def reset_stats(self) -> bool:
        """Reset processing statistics."""
        return bool(self.api_request("/stats/reset", "POST"))

    def get_configuration(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.api_request("/config")


def render_header(dashboard: EmailAgentDashboard):
    """Render dashboard header."""
    st.title("🤖 AI Email Agent Dashboard")
    st.markdown("Control and monitor your automated email processing system")


def render_status_overview(dashboard: EmailAgentDashboard):
    """Render status overview cards."""
    st.subheader("📊 System Status")

    # Get current status
    health = dashboard.get_health_status()
    status = dashboard.get_monitoring_status()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status_class = "status-running" if health.get("status") == "healthy" else "status-stopped"
        st.markdown(f"""
        <div class="metric-card {status_class}">
            <h4>System Health</h4>
            <h2>{health.get('status', 'Unknown').upper()}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        monitoring_status = status.get('monitoring_active', False)
        status_class = "status-running" if monitoring_status else "status-stopped"
        status_text = "RUNNING" if monitoring_status else "STOPPED"
        st.markdown(f"""
        <div class="metric-card {status_class}">
            <h4>Monitoring</h4>
            <h2>{status_text}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        stats = dashboard.get_processing_stats()
        total_processed = stats.get('stats', {}).get('total_processed', 0)
        st.markdown(f"""
        <div class="metric-card">
            <h4>Emails Processed</h4>
            <h2>{total_processed:,}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        last_check = status.get('last_check_time')
        if last_check:
            last_check_dt = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
            time_ago = datetime.now(last_check_dt.tzinfo) - last_check_dt
            time_str = f"{time_ago.seconds // 60} min ago"
        else:
            time_str = "Never"

        st.markdown(f"""
        <div class="metric-card">
            <h4>Last Check</h4>
            <h2>{time_str}</h2>
        </div>
        """, unsafe_allow_html=True)


def render_control_panel(dashboard: EmailAgentDashboard):
    """Render control panel for managing the agent."""
    st.subheader("🎛️ Control Panel")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Monitoring Control")

        # Get current monitoring status
        status = dashboard.get_monitoring_status()
        is_monitoring = status.get('monitoring_active', False)

        if is_monitoring:
            if st.button("⏹️ Stop Monitoring", type="secondary"):
                if dashboard.stop_monitoring():
                    st.success("Monitoring stopped successfully!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to stop monitoring")
        else:
            interval = st.slider("Check Interval (minutes)", 1, 60, 5)
            if st.button("▶️ Start Monitoring", type="primary"):
                if dashboard.start_monitoring(interval):
                    st.success(f"Monitoring started with {interval} minute intervals!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to start monitoring")

        st.markdown("### Manual Actions")

        col2a, col2b = st.columns(2)
        with col2a:
            limit = st.number_input("Email Limit", min_value=1, max_value=50, value=10)

        with col2b:
            dry_run = st.checkbox("Dry Run", help="Don't actually send responses")

        col2a, col2b = st.columns(2)
        with col2a:
            if st.button("🔄 Process Emails", type="primary"):
                with st.spinner("Processing emails..."):
                    result = dashboard.process_emails(limit, dry_run)
                    if result:
                        st.success(f"Processed {result.get('processed', 0)} emails!")
                        st.json(result)
                    else:
                        st.error("Failed to process emails")

        with col2b:
            if st.button("🗑️ Reset Stats", type="secondary"):
                if dashboard.reset_stats():
                    st.success("Statistics reset successfully!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to reset statistics")

    with col2:
        st.markdown("### Quick Actions")

        if st.button("🚀 Immediate Check"):
            result = dashboard.api_request("/emails/check-immediate", "POST")
            if result:
                st.success(f"Immediate check scheduled! Job ID: {result.get('job_id')}")
            else:
                st.error("Failed to schedule immediate check")

        if st.button("🔄 Refresh Status"):
            st.rerun()

        st.markdown("### Configuration")

        config = dashboard.get_configuration()
        if config:
            with st.expander("View Current Configuration"):
                st.json(config)


def render_statistics(dashboard: EmailAgentDashboard):
    """Render statistics and charts."""
    st.subheader("📈 Statistics & Analytics")

    # Get statistics
    stats = dashboard.get_processing_stats()
    status = dashboard.get_monitoring_status()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Processing Statistics")

        if stats and stats.get('stats'):
            stats_data = stats['stats']

            # Create metrics
            metric_col1, metric_col2, metric_col3 = st.columns(3)

            with metric_col1:
                st.metric("Total Processed", stats_data.get('total_processed', 0))

            with metric_col2:
                st.metric("Successful Responses", stats_data.get('successful_responses', 0))

            with metric_col3:
                st.metric("Failed Responses", stats_data.get('failed_responses', 0))

            # Create pie chart for processing results
            total = stats_data.get('total_processed', 0)
            if total > 0:
                successful = stats_data.get('successful_responses', 0)
                failed = stats_data.get('failed_responses', 0)
                skipped = stats_data.get('skipped_emails', 0)

                # Create pie chart
                fig = go.Figure(data=[go.Pie(
                    labels=['Successful', 'Failed', 'Skipped'],
                    values=[successful, failed, skipped],
                    hole=0.3
                )])

                fig.update_layout(title="Processing Results Distribution")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No processing statistics available yet")

    with col2:
        st.markdown("### System Information")

        if status:
            # Create gauge chart for monitoring status
            is_monitoring = status.get('monitoring_active', False)

            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = 1 if is_monitoring else 0,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Monitoring Status"},
                delta = {'reference': 1},
                gauge = {
                    'axis': {'range': [None, 1]},
                    'bar': {'color': "green" if is_monitoring else "red"},
                    'steps': [
                        {'range': [0, 0.5], 'color': "lightgray"},
                        {'range': [0.5, 1], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 0.9
                    }
                }
            ))

            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

            # Show active jobs
            active_jobs = status.get('active_jobs', [])
            if active_jobs:
                st.markdown("### Active Scheduled Jobs")
                for job in active_jobs:
                    job_name = job.get('name', 'Unknown')
                    next_run = job.get('next_run_time', 'Unknown')
                    st.write(f"**{job_name}**: {next_run}")


def render_logs(dashboard: EmailAgentDashboard):
    """Render logs and recent activity."""
    st.subheader("📋 Recent Activity")

    # Get status for recent processing history
    status = dashboard.get_monitoring_status()

    if status and status.get('recent_processing_history'):
        history = status['recent_processing_history']

        # Convert to DataFrame for better display
        df = pd.DataFrame(history)

        if not df.empty:
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp', ascending=False)

            # Display recent processing runs
            st.markdown("### Recent Processing Runs")

            for _, row in df.iterrows():
                with st.expander(f"📧 {row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"):
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Processed", row['processed'])

                    with col2:
                        st.metric("Responded", row['responded'])

                    with col3:
                        st.metric("Skipped", row['skipped'])

                    with col4:
                        st.metric("Time", f"{row['processing_time']:.2f}s")
        else:
            st.info("No recent processing activity")
    else:
        st.info("No recent processing activity available")


def render_sidebar(dashboard: EmailAgentDashboard):
    """Render sidebar with additional controls."""
    st.sidebar.markdown("## ⚙️ Settings")

    # API Configuration
    st.sidebar.markdown("### API Configuration")
    api_url = st.sidebar.text_input("API URL", value=API_BASE_URL)

    if api_url != API_BASE_URL:
        dashboard.api_url = api_url

    # Refresh interval
    st.sidebar.markdown("### Auto Refresh")
    auto_refresh = st.sidebar.checkbox("Enable Auto Refresh")

    if auto_refresh:
        refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 10, 120, 30)
        st.sidebar.markdown(f"Page will refresh every {refresh_interval} seconds")

        # Auto refresh using st.rerun()
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = time.time()

        if time.time() - st.session_state.last_refresh > refresh_interval:
            st.session_state.last_refresh = time.time()
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Quick Links")

    if st.sidebar.button("📚 API Documentation"):
        st.info("API docs available at: http://localhost:8000/docs")

    if st.sidebar.button("🏠 Health Check"):
        health = dashboard.get_health_status()
        st.sidebar.json(health)


def main():
    """Main dashboard application."""
    # Initialize dashboard
    dashboard = EmailAgentDashboard()

    # Render sidebar
    render_sidebar(dashboard)

    # Render main components
    render_header(dashboard)
    render_status_overview(dashboard)

    # Control Panel and Statistics
    col1, col2 = st.columns([1, 1])

    with col1:
        render_control_panel(dashboard)

    with col2:
        render_statistics(dashboard)

    # Logs section
    render_logs(dashboard)

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "AI Email Agent Dashboard - Built with Streamlit ❤️"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()