import streamlit as st
import pandas as pd
import re
import requests  # Clean, native network tool

# 1. Page configuration must be the absolute first execution layer!
st.set_page_config(
    page_title="Korean Video Clips", 
    page_icon="📺", 
    layout="wide"
)

# ⚙️ SECURE ENDPOINT CONFIGURATION
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_ANON_KEY"]

# 💉 INJECT CUSTOM CSS TO FREEZE THE TITLE, REMOVE PADDING, AND RESIZE SPACING
st.markdown("""
    <style>
        /* Global Page Padding Reduction & Alignment */
        .block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 0rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }

        /* Standard top bar spacing to accommodate native mobile controls */
        [data-testid="stHeader"] {
            background-color: transparent !important;
        }
        
        /* Sidebar collapse alignment */
        [data-testid="stSidebarCollapseButton"] {
            margin-top: 0.5rem !important;
            margin-left: 0.5rem !important;
        }

        /* DYNAMICALLY ANCHORED FROZEN TITLE AREA */
        [data-testid="stMainView"] {
            display: flex;
            flex-direction: column;
        }
        
        .frozen-title {
            position: sticky;
            top: 0;
            
            z-index: 99;
            padding-top: 1rem;
            padding-bottom: 0.8rem;
            border-bottom: 1px solid #31333F;
            width: 100%;
        }
        
        /* Push Sidebar Elements to the absolute top */
        [data-testid="stSidebarUserContent"] {
            padding-top: 0.5rem !important;
        }
        
        /* Tighten spacing layout metrics */
        hr {
            margin-top: 0.5rem !important;
            margin-bottom: 0.5rem !important;
        }
        .element-container {
            margin-bottom: 0.5rem !important;
        }
    </style>
""", unsafe_allow_html=True)


# 🔄 Fetch data natively via standard HTTPS REST request
@st.cache_data(ttl=5)
def load_data():
    try:
        # Build the direct URL endpoint to your table matrix
        endpoint = f"{url}/rest/v1/korean_clips"
        
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}"
        }
        
        # Fire a secure GET network call directly to Supabase
        response = requests.get(endpoint, headers=headers)
        
        if response.status_code == 200:
            records = response.json()
            if records:
                return pd.DataFrame(records)
        else:
            st.error(f"Database returned status code: {response.status_code}")
            
        return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Error loading data layers from database: {e}")
        return pd.DataFrame()


# Helper function to convert raw seconds to a readable HH:MM:SS or MM:SS string
def format_time(seconds):
    if pd.isna(seconds) or seconds is None or str(seconds).strip() == "":
        return ""
    try:
        seconds = int(float(seconds))
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    except:
        return str(seconds)


# Helper function to extract standard YouTube ID for embeds
def extract_youtube_id(url):
    if not isinstance(url, str):
        return None
    pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None


# Fetch production data 
video_data = load_data()

if not video_data.empty:
    # Handle optional column configurations safely if instructors filter items away
    hide_conditions = ['hide', 'Hide']
    visible_data = video_data.copy()
    
    for col in ['hide', 'display', 'visibility']:
        if col in visible_data.columns:
            visible_data = visible_data[~visible_data[col].astype(str).str.strip().isin(hide_conditions)]

    # 📌 RENDER FROZEN STICKY HEADER
    st.markdown("""
        <div class="frozen-title">
            <h1 style="margin:0; padding: 10px 0px 0px 5px; font-size: 1.5rem;">📺 Korean Video Clips</h1>
            <p style="margin:0; padding: 0px 0px 0px 5px; font-size: 0.95rem; color: #a3a8b4;">A collaborative language video archive.</p>
        </div>
    """, unsafe_allow_html=True)

    # --- SIDEBAR NAVIGATION FILTER CONTROLS ---
    st.sidebar.header("Filter Material")
    
    if 'level' in visible_data.columns:
        unique_levels = visible_data['level'].dropna().unique().tolist()
        unique_levels = [str(x).strip() for x in unique_levels if str(x).strip()]
        unique_levels.sort()
        selected_level = st.sidebar.selectbox("Select Proficiency Level", ["-- Choose a Level --"] + unique_levels)
    else:
        selected_level = "-- Choose a Level --"
        st.sidebar.warning("Add a 'level' column to your Supabase table to sort entries by proficiency.")

    selected_lesson = "-- Choose a Lesson --"
    selected_grammar = "-- Choose Grammar --"

    if selected_level == "-- Choose a Level --":
        st.sidebar.info("Select a proficiency level first.")
        
    else:
        level_filtered = visible_data[visible_data['level'].astype(str).str.strip() == selected_level]
        if 'lesson' in level_filtered.columns:
            unique_lessons = level_filtered['lesson'].dropna().unique().tolist()
            unique_lessons = [str(x).strip() for x in unique_lessons if str(x).strip()]
            
            def lesson_sort_key(s):
                s_lower = str(s).lower()
                if 'news' in s_lower or 'media' in s_lower: return (0, s)
                if 'beg' not in s_lower and 'int' not in s_lower: return (1, s)
                if 'beg' in s_lower:
                    num = re.findall(r'\d+', s)
                    return (2, int(num[0]) if num else 0)
                if 'int' in s_lower:
                    num = re.findall(r'\d+', s)
                    return (3, int(num[0]) if num else 0)
                return (4, s)
            unique_lessons.sort(key=lesson_sort_key)
            
            selected_lesson = st.sidebar.selectbox("Select Lesson", ["-- Choose a Lesson --"] + unique_lessons)

        if selected_lesson == "-- Choose a Lesson --" and selected_level != "-- Choose a Level --":
            st.sidebar.info("Select a lesson to see grammar patterns.")
            
        elif selected_lesson != "-- Choose a Lesson --":
            lesson_filtered = level_filtered[level_filtered['lesson'].astype(str).str.strip() == selected_lesson]
            if 'grammar_point' in lesson_filtered.columns:
                unique_grammar = lesson_filtered['grammar_point'].dropna().unique().tolist()
                unique_grammar = [str(x).strip() for x in unique_grammar if str(x).strip()]
                unique_grammar.sort()
                
                selected_grammar = st.sidebar.selectbox("Select Grammar Point", ["-- Choose Grammar --"] + unique_grammar)

    # --- MAIN CONTENT WORKSPACE PANEL ---
    st.markdown('<div class="main-content-wrapper">', unsafe_allow_html=True)

    if selected_level != "-- Choose a Level --" and selected_lesson != "-- Choose a Lesson --" and selected_grammar != "-- Choose Grammar --":
        final_filtered = visible_data[
            (visible_data['level'].astype(str).str.strip() == selected_level) &
            (visible_data['lesson'].astype(str).str.strip() == selected_lesson) & 
            (visible_data['grammar_point'].astype(str).str.strip() == selected_grammar)
        ]
        
        st.markdown(
            f'<p style="font-size: 24px; font-weight: 600; margin-bottom: 0px;">'
            f'Lesson: {selected_level}, {selected_lesson}, {selected_grammar}'
            f'</p>', 
            unsafe_allow_html=True
        )        
   
        st.markdown(
            f'<p style="font-size: 0.85rem; color: #a3a8b4; margin-top: 0px; margin-bottom: 15px;">'
            f'Matches found: {len(final_filtered)}'
            f'</p>',
            unsafe_allow_html=True
        )

        st.divider()

        for idx, row in final_filtered.iterrows():
            video_id = extract_youtube_id(row['youtube_link'])
            if video_id:
                try:
                    start_time = int(float(row['start'])) if pd.notna(row['start']) and str(row['start']).strip() != "" else 0
                except:
                    start_time = 0
                    
                try:
                    end_time = int(float(row['end'])) if pd.notna(row['end']) and str(row['end']).strip() != "" else None
                except:
                    end_time = None
                
                if end_time and end_time <= start_time:
                    end_time = None
                
                start_formatted = format_time(start_time)
                end_formatted = format_time(end_time) if end_time else None
                
                embed_url = f"https://www.youtube-nocookie.com/embed/{video_id}?start={start_time}&rel=0&modestbranding=1"
                if end_time:
                    embed_url += f"&end={end_time}"
                
                state_key = f"replay_{video_id}_{idx}"
                if state_key not in st.session_state:
                    st.session_state[state_key] = 0

                with st.container(key=f"container_{video_id}_{idx}_{st.session_state[state_key]}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.components.v1.html(
                            f'''
                            <iframe 
                                width="100%" 
                                height="550" 
                                src="{embed_url}" 
                                title="YouTube video player" 
                                frameborder="0" 
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                                allowfullscreen
                                sandbox="allow-scripts allow-same-origin allow-popups allow-presentation">
                            </iframe>
                            ''',
                            height=550
                        )
                    
                    with col2:
                        time_display = f"`{start_formatted}`" + (f" to `{end_formatted}`" if end_formatted else "")
                        st.markdown(f"**📍Timestamp:** {time_display}")
                        
                        if st.button("🔁 Replay Clip", key=f"btn_{video_id}_{idx}"):
                            st.session_state[state_key] += 1
                            st.rerun()
                        
                        if 'korean_text' in row and pd.notna(row['korean_text']) and str(row['korean_text']).strip() != "":
                            with st.expander("Show Korean Transcript", expanded=False):
                                st.write(row['korean_text'])
                                
                        if 'english_text' in row and pd.notna(row['english_text']) and str(row['english_text']).strip() != "":
                            with st.expander("Show English Translation", expanded=False):
                                st.write(row['english_text'])
                                
                st.markdown("---")
    else:
        st.info("💡 Please refine your selection in the left sidebar menu to populate video clips.")
        
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.warning("No data found inside your Supabase 'korean_clips' table framework.")
