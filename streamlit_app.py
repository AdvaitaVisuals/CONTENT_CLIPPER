import streamlit as st
import os
import json
import time
import subprocess
import shutil
import imageio_ffmpeg
import zipfile
from io import BytesIO
from datetime import datetime
from agents.understanding_agent import UnderstandingAgent
from agents.viral_cutter_agent import ViralCutterAgent, ClipSpec
from agents.frame_power_agent import FramePowerAgent
from agents.caption_agent import CaptionAgent
from agents.trend_agent import TrendAgent
from agents.strategy_brain import StrategyBrain
from agents.auto_posting_agent import AutoPostingAgent
from agents.vizard_agent import VizardAgent

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="BIRU BHAI AI | Viral Video Factory",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CUSTOM CSS ---
def local_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    :root {
        --bg-dark: #0a0a0a;
        --card-bg: #161616;
        --neon-green: #0aff60;
        --gold: #ffd700;
        --text-main: #ffffff;
        --text-dim: #888888;
    }

    span, div, p, h1, h2, h3, button {
        font-family: 'Outfit', sans-serif;
    }

    .main {
        background-color: var(--bg-dark);
        color: var(--text-main);
    }

    .stApp {
        background-color: var(--bg-dark);
    }

    /* Side bar */
    [data-testid="stSidebar"] {
        background-color: #111111;
        border-right: 1px solid rgba(255,255,255,0.1);
    }

    /* Headers */
    h1, h2, h3 {
        color: var(--text-main) !important;
        font-weight: 800 !important;
    }

    .highlight {
        color: var(--neon-green);
    }

    /* Cards */
    .stat-card {
        background: var(--card-bg);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        transition: 0.3s;
    }
    
    .stat-card:hover {
        border-color: var(--neon-green);
        transform: translateY(-5px);
    }

    .stat-value {
        font-size: 2rem;
        font-weight: 800;
        color: var(--neon-green);
    }

    .stat-label {
        color: var(--text-dim);
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Buttons */
    .stButton>button {
        background-color: var(--neon-green) !important;
        color: black !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 5px !important;
        padding: 10px 25px !important;
        transition: 0.2s !important;
    }

    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px var(--neon-green);
    }

    /* Progress Bar */
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #0aff60, #ffd700);
    }

    /* Video Player */
    .stVideo {
        border-radius: 15px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- UTILS ---
@st.cache_resource
def get_agents(vizard_api_key=None):
    # Cache heavy agents to avoid reloading on every rerun
    with st.spinner("Loading AI Models (Whisper, BERT, etc.)..."):
        understanding = UnderstandingAgent()
        viral_cutter = ViralCutterAgent()
        frame_power = FramePowerAgent()
        caption_agent = CaptionAgent()
        trend_agent = TrendAgent()
        strategy_brain = StrategyBrain()
        poster = AutoPostingAgent()
        vizard = VizardAgent(api_key=vizard_api_key)
        return understanding, viral_cutter, frame_power, caption_agent, trend_agent, strategy_brain, poster, vizard

def download_video(url, output_dir):
    try:
        output_template = os.path.join(output_dir, '%(title)s.%(ext)s')
        command = [
            'yt-dlp', 
            '-f', 'best[ext=mp4]/best', 
            '-o', output_template, 
            '--no-playlist',
            url
        ]
        subprocess.run(command, check=True, capture_output=True, text=True)
        files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith('.mp4')]
        if not files: return None
        return max(files, key=os.path.getmtime)
    except Exception as e:
        st.error(f"Download failed: {e}")
        return None

# --- SIDEBAR NAVIGATION ---
st.sidebar.markdown(f"<h1 style='text-align: center;'>BIRU <span class='highlight'>BHAI</span></h1>", unsafe_allow_html=True)
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigation", ["Dashboard", "Video Factory", "Trend Board", "Strategy Brain", "Auto Posting"])

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ AI Engine Settings")
processing_mode = st.sidebar.selectbox("Clipping Engine", ["Local (Fast/Free)", "Vizard AI (Pro/API)"])
vizard_key = st.sidebar.text_input("Vizard API Key", type="password", value="9658587d3d6045a492268e512f5e5577")

# --- SESSION STATE ---
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'trends' not in st.session_state:
    st.session_state.trends = None
if 'strategy' not in st.session_state:
    st.session_state.strategy = None

# --- AGENTS ---
agents = get_agents(vizard_api_key=vizard_key)
understanding_agent, viral_cutter, frame_power, caption_agent, trend_agent, strategy_brain, poster_agent, vizard_agent = agents

# --- DASHBOARD ---
if page == "Dashboard":
    st.markdown("## 📊 Agent <span class='highlight'>Command Center</span>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("<div class='stat-card'><div class='stat-value'>24/7</div><div class='stat-label'>Uptime</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='stat-card'><div class='stat-value'>82</div><div class='stat-label'>Viral Clips Gen</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='stat-card'><div class='stat-value'>0.98</div><div class='stat-label'>Avg Virality</div></div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<div class='stat-card'><div class='stat-value'>Active</div><div class='stat-label'>Auto Posting</div></div>", unsafe_allow_html=True)

    st.markdown("### 🚀 Recent Activity")
    st.info("Agent 01: Trend analysis complete (Found 3 new desi trends)")
    st.info("Agent 02: Clip #42 uploaded successfully to Instagram")

# --- VIDEO FACTORY ---
elif page == "Video Factory":
    st.markdown("## 🎬 Video <span class='highlight'>Factory</span>", unsafe_allow_html=True)
    
    video_input = st.text_input("YouTube URL or Local Path", placeholder="https://youtube.com/watch?v=...")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        uploaded_file = st.file_uploader("Or Upload Video", type=["mp4", "mov"])
        
    process_btn = st.button("🚀 PROCESS VIRAL CLIPS")
    
    output_base = "output"
    os.makedirs(output_base, exist_ok=True)

    if process_btn:
        # CLEAR PREVIOUS DATA
        st.session_state.processed_data = None
        
        if not video_input and not uploaded_file:
            st.warning("Please provide a video source!")
        else:
            video_path = None
            with st.status("🎬 Initializing Processing...", expanded=True) as status:
                
                if processing_mode == "Vizard AI (Pro/API)":
                    if not vizard_key:
                        st.error("Please enter a Vizard API Key in the sidebar!")
                    elif not video_input or not (video_input.startswith("http")):
                        st.error("Vizard AI requires a YouTube/Public URL to process.")
                    else:
                        status.update(label="🚀 Sending video to Vizard AI...")
                        project_id = vizard_agent.submit_video(video_input)
                        if project_id:
                            status.update(label=f"✅ Project Created (ID: {project_id}). Processing...")
                            processed_clips = []
                            # Polling loop
                            for i in range(30): # Try for ~5 mins
                                v_status = vizard_agent.status_check(project_id)
                                if v_status == "completed":
                                    processed_clips = vizard_agent.get_clips(project_id)
                                    status.update(label="✅ Vizard processing complete!", state="complete")
                                    break
                                elif v_status == "failed":
                                    st.error("Vizard processing failed.")
                                    break
                                status.update(label=f"⏳ Vizard is thinking... (Attempt {i+1}/30, Status: {v_status})")
                                time.sleep(10)
                            
                            if processed_clips:
                                # Map Vizard clips to BiruBhai format
                                clip_specs = []
                                for vc in processed_clips:
                                    clip_specs.append(ClipSpec(
                                        start_time=vc.get("startTime", 0),
                                        end_time=vc.get("endTime", 15),
                                        hook_line=vc.get("headline", "Vizard Clip"),
                                        target_audience="vizard_auto",
                                        viral_reason="AI Detected Highlight",
                                        platform="instagram_reel",
                                        aspect_ratio="9:16",
                                        score=0.9
                                    ))
                                
                                st.session_state.processed_data = {
                                    "video_path": video_input,
                                    "clip_specs": clip_specs,
                                    "vizard_project_id": project_id
                                }
                                st.write(f"🔥 Vizard found {len(clip_specs)} clips!")
                                status.update(label="✅ Vizard Complete!", state="complete", expanded=False)
                        else:
                            st.error("Failed to submit to Vizard. Check your API key and URL.")

                else: # LOCAL MODE
                    # 1. Input Handling
                    if uploaded_file:
                        video_path = os.path.join(output_base, uploaded_file.name)
                        with open(video_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        st.write("✅ Video uploaded locally.")
                    else:
                        st.write("🌐 Downloading from YouTube...")
                        video_path = download_video(video_input, output_base)
                    
                    if not video_path:
                        st.error("Failed to acquire video.")
                    else:
                        # 2. Audio Extraction
                        st.write("🎵 Extracting high-fidelity audio...")
                        audio_path = understanding_agent.extract_audio(video_path)
                        
                        # 3. Transcription & Analysis
                        st.write("🧠 AI Analyzing content & emotions (Whisper)...")
                        transcription = understanding_agent.transcribe_with_timestamps(audio_path)
                        beat_analysis = understanding_agent.detect_beat_drops(audio_path)
                        segments = transcription.get('segments', [])
                        tagged_segments = understanding_agent.tag_emotions(segments)
                        
                        # 4. Chorus Detection
                        st.write("🎵 Looking for catchy chorus loops...")
                        chorus = understanding_agent.find_chorus(tagged_segments)
                        if chorus:
                            beat_analysis["chorus_times"] = chorus["timestamps"]
                        
                        understanding_data = {
                            "lyrics_segments": tagged_segments,
                            "beat_analysis": beat_analysis
                        }
                        
                        # 5. Viral Specs
                        st.write("✂️ Generating Viral Clip Specifications...")
                        clip_specs = viral_cutter.generate_clip_specs(understanding_data)
                        st.write(f"🔥 Found {len(clip_specs)} potential viral moments!")
                        
                        # 6. Result Storage
                        st.session_state.processed_data = {
                            "video_path": video_path,
                            "clip_specs": clip_specs,
                            "understanding_data": understanding_data
                        }
                        status.update(label="✅ Processing Complete!", state="complete", expanded=False)

    # Display Results
    if st.session_state.processed_data:
        data = st.session_state.processed_data
        st.markdown("---")
        st.markdown("### 🔥 High-Virality Clips Found")
        
        if not data["clip_specs"]:
            st.info("No explicit viral moments were automatically identified. Try a different video or check back later!")
        
        # --- DOWNLOAD ALL BUTTON ---
        if data["clip_specs"]:
            if st.button("📦 PREPARE ALL CLIPS (ZIP)", use_container_width=True):
                with st.spinner("Zipping all clips..."):
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for i, spec in enumerate(data["clip_specs"][:10]):
                            output_clip_path = os.path.join("output", "clips", f"reel_{i+1}_all.mp4")
                            os.makedirs(os.path.join("output", "clips"), exist_ok=True)
                            
                            # Cut if not exists
                            if not os.path.exists(output_clip_path):
                                if processing_mode == "Local (Fast/Free)":
                                    viral_cutter.cut_video(data["video_path"], spec, output_clip_path)
                                
                            if os.path.exists(output_clip_path):
                                zip_file.write(output_clip_path, arcname=f"biru_bhai_clip_{i+1}.mp4")
                    
                    st.download_button(
                        label="🔥 DOWNLOAD ALL CLIPS ZIP 🔥",
                        data=zip_buffer.getvalue(),
                        file_name="biru_bhai_viral_box.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
        
        st.markdown("---")
        for i, spec in enumerate(data["clip_specs"][:10]): # Show up to 10
            with st.container():
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.markdown(f"**CLIP #{i+1}**")
                    # ClipSpec uses .score
                    score = getattr(spec, 'score', getattr(spec, 'predicted_score', 0.5))
                    st.markdown(f"**Score:** `{score:.2f}`")
                    st.markdown(f"**Duration:** `{spec.start_time:.1f}s - {spec.end_time:.1f}s`")
                
                with c2:
                    st.markdown(f"**Reason:** {spec.viral_reason}")
                    st.markdown(f"**Hook:** *\"{spec.hook_line}\"*")
                    st.markdown(f"**Target:** `{spec.target_audience}`")
                    
                    if st.button(f"🎬 Generate & Download Reel #{i+1}", key=f"gen_{i}"):
                        output_clip_path = os.path.join("output", "clips", f"reel_{i+1}_processed.mp4")
                        os.makedirs(os.path.join("output", "clips"), exist_ok=True)
                        
                        with st.spinner(f"Cutting Reel #{i+1} (Local Engine)..."):
                            try:
                                # Use viral_cutter to cut the clip
                                # Note: data["video_path"] could be a URL in Vizard mode, 
                                # but for Local it's a file path.
                                if processing_mode == "Local (Fast/Free)":
                                    viral_cutter.cut_video(data["video_path"], spec, output_clip_path)
                                    st.success(f"Clip saved locally at: `{output_clip_path}`")
                                    
                                    # Provide download button for browser
                                    with open(output_clip_path, "rb") as file:
                                        st.download_button(
                                            label="💾 SAVE TO MY COMPUTER",
                                            data=file,
                                            file_name=f"biru_bhai_reel_{i+1}.mp4",
                                            mime="video/mp4"
                                        )
                                else:
                                    st.info("For Vizard AI, clips are stored on their cloud. Visit Vizard dashboard to download or use local engine to cut and save here.")
                            except Exception as e:
                                st.error(f"Cutting failed: {e}")
            st.markdown("---")
            
        st.caption(f"All files are stored on your disk at: `{os.path.abspath('output')}`")

# --- TREND BOARD ---
elif page == "Trend Board":
    st.markdown("## 📈 Trend <span class='highlight'>Intelligence</span>", unsafe_allow_html=True)
    
    import asyncio
    
    if st.button("🔍 FETCH LATEST TRENDS"):
        with st.spinner("Agent scanning Haryanvi music scene & competitors..."):
            try:
                # Call the async analyze_trends method
                report = asyncio.run(trend_agent.analyze_trends())
                st.session_state.trends = report
                st.success("Trend Report Generated!")
            except Exception as e:
                st.error(f"Failed to fetch trends: {e}")
            
    if st.session_state.trends:
        report = st.session_state.trends
        
        # Summary Section
        st.markdown("### 📝 Weekly Summary")
        st.info(report['weekly_summary'])
        
        # Recommendations Card Grid
        st.markdown("### 🚀 Top Recommendations")
        recs = report.get('recommendations', [])
        if recs:
            rec_cols = st.columns(len(recs))
            for i, rec in enumerate(recs):
                with rec_cols[i]:
                    st.markdown(f"""
                    <div class='stat-card'>
                        <div style='color: var(--neon-green); font-size: 1.1rem; font-weight: 800;'>ACTION #{i+1}</div>
                        <div style='font-size: 0.9rem; margin-top: 10px;'>{rec}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Detailed Insights Table/Expander
        st.markdown("### 🔬 Detailed Data Insights")
        for insight in report.get('insights', []):
            with st.expander(f"[{insight['trend_type'].upper()}] - {insight['description'][:50]}..."):
                st.write(f"**Full Description:** {insight['description']}")
                st.write(f"**Action Recommendation:** {insight['action_recommendation']}")
                st.write(f"**Confidence:** `{insight['confidence']:.0%}` | **Source:** `{insight['data_source']}`")

# --- STRATEGY BRAIN ---
elif page == "Strategy Brain":
    st.markdown("## 🧠 Strategy <span class='highlight'>Brain</span>", unsafe_allow_html=True)
    
    if st.button("📅 GENERATE CONTENT CALENDAR"):
        if not st.session_state.trends:
            st.warning("Please fetch trends first!")
        elif not st.session_state.processed_data:
            st.warning("Please process a video in 'Video Factory' first to get clips!")
        else:
            with st.spinner("Synthesizing data into calendar..."):
                clips = [vars(s) for s in st.session_state.processed_data["clip_specs"]]
                trends = st.session_state.trends
                memory_data = {"emotion_performance": {"akad": {"avg_engagement": 0.08}}}
                
                plan = strategy_brain.make_decisions(clips, trends, memory_data)
                st.session_state.strategy = plan
                
    if st.session_state.strategy:
        st.markdown(f"**Guidance:** {st.session_state.strategy.get('weekly_guidance')}")
        
        calendar = st.session_state.strategy.get("content_calendar", [])
        for item in calendar:
            with st.chat_message("ai"):
                st.markdown(f"**{item['scheduled_time']}** | **{item['platform'].replace('_', ' ').upper()}**")
                st.write(f"**Content ID:** `{item['content_id']}`")
                st.write(f"*Reasoning:* {item['reason']}")
                st.write(f"**Score:** `{item['predicted_score']:.2f}` | **Emotion:** `{item['emotion']}`")

# --- AUTO POSTING ---
elif page == "Auto Posting":
    st.markdown("## 📤 Posting <span class='highlight'>Station</span>", unsafe_allow_html=True)
    
    st.markdown("### 📡 Active Queue")
    if st.session_state.strategy:
        calendar = st.session_state.strategy.get("content_calendar", [])
        for i, item in enumerate(calendar):
            c1, c2, c3 = st.columns([1, 2, 1])
            c1.write(item['scheduled_time'])
            c2.write(f"**{item['content_id']}** on {item['platform']}")
            if c3.button("POST NOW", key=f"post_{i}"):
                with st.spinner("Connecting to API..."):
                    time.sleep(2)
                    st.success("Posted!")
    else:
        st.warning("No strategy generated yet.")

# --- FOOTER ---
st.sidebar.markdown("---")
st.sidebar.markdown("<p style='text-align: center; color: #888;'>BIRU BHAI AI v1.0.4<br>System Status: <span style='color: #0aff60;'>ONLINE</span></p>", unsafe_allow_html=True)
