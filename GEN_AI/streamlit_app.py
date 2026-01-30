"""Streamlit Web Interface for Pet Roast AI Service - Local Testing."""

import streamlit as st
import requests
import time
from PIL import Image
import io
import base64

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="Pet Roast AI - Local Test",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #FF6B6B;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        text-align: center;
        color: #4ECDC4;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #FF6B6B;
        color: white;
        font-size: 1.2rem;
        font-weight: bold;
        border-radius: 10px;
        padding: 0.75rem;
        border: none;
    }
    .stButton>button:hover {
        background-color: #FF5252;
    }
    .success-box {
        padding: 1rem;
        border-radius: 10px;
        background-color: #D4EDDA;
        border: 2px solid #28A745;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 10px;
        background-color: #F8D7DA;
        border: 2px solid #DC3545;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 10px;
        background-color: #D1ECF1;
        border: 2px solid #17A2B8;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)


def check_api_health():
    """Check if the API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/healthz", timeout=5)
        return response.status_code == 200
    except:
        return False


def get_banuba_filters():
    """Get available Banuba filters."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/banuba-filters", timeout=5)
        if response.status_code == 200:
            return response.json().get("filters", [])
        return []
    except:
        return []


def upload_image_to_url(uploaded_file):
    """Convert uploaded file to base64 data URL."""
    try:
        bytes_data = uploaded_file.getvalue()
        base64_encoded = base64.b64encode(bytes_data).decode('utf-8')
        mime_type = uploaded_file.type
        return f"data:{mime_type};base64,{base64_encoded}"
    except Exception as e:
        st.error(f"Error processing image: {e}")
        return None


def generate_video(text, image_url, filter_id=None):
    """Generate a pet roast video."""
    # Use image_data for base64 data URLs to avoid URL length limits
    if image_url and image_url.startswith("data:image/"):
        payload = {
            "text": text,
            "image_data": image_url  # Send base64 data directly
        }
    else:
        payload = {
            "text": text,
            "image_url": image_url
        }
    if filter_id:
        payload["filter_id"] = filter_id

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/generate-video",
            json=payload,
            timeout=30
        )
        return response.status_code, response.json()
    except Exception as e:
        return 500, {"error": str(e)}


def check_video_status(job_id):
    """Check the status of a video generation job."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/video-status/{job_id}",
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


def get_video_result(job_id):
    """Get the final video result."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/video-result/{job_id}",
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


# Main App
def main():
    # Header
    st.markdown('<div class="main-header">🐾 Pet Roast AI 🎬</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Generate hilarious roast videos of your pets!</div>', unsafe_allow_html=True)

    # Sidebar - System Status
    with st.sidebar:
        st.header("🔧 System Status")

        if check_api_health():
            st.markdown('<div class="success-box">✅ API Server: Online</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="error-box">❌ API Server: Offline<br/>Please start the server!</div>', unsafe_allow_html=True)
            st.code("uvicorn app.main:app --reload --host 0.0.0.0 --port 8000", language="bash")
            st.warning("⚠️ Some features may not work without the API server running.")

        st.markdown("---")
        st.header("📚 Quick Links")
        st.markdown(f"[API Documentation]({API_BASE_URL}/docs)")
        st.markdown(f"[Health Check]({API_BASE_URL}/healthz)")

        st.markdown("---")
        st.header("ℹ️ How It Works")
        st.markdown("""
        1. **Upload** a pet image
        2. **Enter** your roast text
        3. **Select** an AR filter (optional)
        4. **Generate** your video
        5. **Download** and share!
        """)

    # Main Content
    tab1, tab2, tab3 = st.tabs(["🎬 Generate Video", "📊 Check Status", "🎨 Available Filters"])

    # Tab 1: Generate Video
    with tab1:
        st.header("Create Your Pet Roast Video")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("📸 Upload Pet Image")
            uploaded_file = st.file_uploader(
                "Choose a pet image (JPG, PNG)",
                type=["jpg", "jpeg", "png"],
                help="Upload a clear image of your pet"
            )

            if uploaded_file:
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Image", width='stretch')

        with col2:
            st.subheader("✍️ Roast Text")
            roast_text = st.text_area(
                "Enter your roast text",
                placeholder="e.g., Look at this lazy furball! Thinks he's a king but can't even catch a mouse!",
                height=150,
                help="Enter the text you want to appear in the video"
            )

            st.subheader("🎨 AR Filter (Optional)")
            filters = get_banuba_filters()

            if filters:
                filter_options = ["None"] + [f"{f['name']} - {f['description']}" for f in filters]
                selected_filter = st.selectbox("Choose an AR filter", filter_options)

                if selected_filter != "None":
                    filter_id = filters[filter_options.index(selected_filter) - 1]["id"]
                else:
                    filter_id = None
            else:
                filter_id = None
                st.info("No filters available")

        st.markdown("---")

        if st.button("🚀 Generate Video", type="primary"):
            if not uploaded_file:
                st.error("⚠️ Please upload a pet image!")
            elif not roast_text.strip():
                st.error("⚠️ Please enter roast text!")
            else:
                with st.spinner("🎬 Generating your video... This may take a moment..."):
                    # Convert image to base64 data URL
                    image_url = upload_image_to_url(uploaded_file)

                    if image_url:
                        status_code, result = generate_video(roast_text, image_url, filter_id)

                        if status_code == 202:
                            job_id = result.get("job_id")
                            st.success(f"✅ Video generation started!")
                            st.markdown(f'<div class="info-box"><strong>Job ID:</strong> {job_id}<br/>Check the status in the "Check Status" tab</div>', unsafe_allow_html=True)

                            # Store job ID in session state
                            if "job_ids" not in st.session_state:
                                st.session_state.job_ids = []
                            st.session_state.job_ids.insert(0, job_id)

                            # Auto-poll for status
                            status_placeholder = st.empty()
                            for i in range(60):  # Poll for up to 60 seconds
                                time.sleep(2)
                                status = check_video_status(job_id)
                                if status:
                                    current_status = status.get("status", "unknown")
                                    status_placeholder.info(f"⏳ Status: {current_status}")

                                    if current_status == "completed":
                                        result = get_video_result(job_id)
                                        if result and result.get("video_url"):
                                            st.success("🎉 Video generated successfully!")
                                            st.video(result["video_url"])
                                        break
                                    elif current_status == "failed":
                                        st.error(f"❌ Generation failed: {status.get('error_message', 'Unknown error')}")
                                        break
                        elif status_code == 400:
                            error_detail = result.get("detail", {})
                            if isinstance(error_detail, dict):
                                st.error(f"❌ {error_detail.get('message', 'Bad request')}")
                                if error_detail.get("suggestion"):
                                    st.info(f"💡 {error_detail['suggestion']}")
                            elif isinstance(error_detail, list):
                                # Pydantic validation errors
                                st.error("❌ Validation Error:")
                                for err in error_detail:
                                    st.write(f"- {err.get('msg', 'Unknown error')}")
                            else:
                                st.error(f"❌ {error_detail}")
                            # Show full response for debugging
                            with st.expander("Show full error details"):
                                st.json(result)
                        else:
                            st.error(f"❌ Error: {result.get('detail', 'Unknown error')}")
                            with st.expander("Show full error details"):
                                st.json(result)

    # Tab 2: Check Status
    with tab2:
        st.header("Check Video Generation Status")

        # Show recent job IDs
        if "job_ids" in st.session_state and st.session_state.job_ids:
            st.subheader("Recent Jobs")
            for job_id in st.session_state.job_ids[:5]:
                with st.expander(f"Job: {job_id}"):
                    if st.button(f"Check Status", key=f"check_{job_id}"):
                        status = check_video_status(job_id)
                        if status:
                            st.json(status)

                            if status.get("status") == "completed":
                                result = get_video_result(job_id)
                                if result and result.get("video_url"):
                                    st.success("✅ Video ready!")
                                    st.video(result["video_url"])
                        else:
                            st.error("Failed to fetch status")

        st.markdown("---")

        # Manual job ID check
        st.subheader("Check Specific Job")
        manual_job_id = st.text_input("Enter Job ID", placeholder="e.g., abc123xyz")

        if st.button("🔍 Check Status"):
            if manual_job_id:
                with st.spinner("Fetching status..."):
                    status = check_video_status(manual_job_id)
                    if status:
                        st.json(status)

                        if status.get("status") == "completed":
                            result = get_video_result(manual_job_id)
                            if result and result.get("video_url"):
                                st.success("✅ Video ready!")
                                st.video(result["video_url"])
                    else:
                        st.error("❌ Job not found or error fetching status")
            else:
                st.warning("Please enter a job ID")

    # Tab 3: Available Filters
    with tab3:
        st.header("Available AR Filters")

        filters = get_banuba_filters()

        if filters:
            cols = st.columns(3)
            for idx, filter_info in enumerate(filters):
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div class="info-box">
                        <h3>🎨 {filter_info['name']}</h3>
                        <p><strong>ID:</strong> {filter_info['id']}</p>
                        <p>{filter_info['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No filters configured")


# Streamlit automatically runs the script, but we can call main() explicitly
# This ensures the app renders even if there are import issues
try:
    main()
except Exception as e:
    st.error(f"Error loading app: {e}")
    st.exception(e)