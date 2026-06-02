import streamlit as st
import pandas as pd
import re

# Set professional page layout with custom media browser tab icon
st.set_page_config(
    page_title="Korean Video Clips", 
    page_icon="📺", 
    layout="wide"
)

# 💉 INJECT CUSTOM CSS TO FREEZE THE TITLE, REMOVE PADDING, AND RESIZE SPACING
# 💉 INJECT SMART DYNAMIC CSS TO ADAPT TO SIDEBAR CHANGES
st.markdown("""
    <style>
        /* 1. Global Page Padding Reduction & Alignment */
        .block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 0rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }
        
            
            

        /* 2. standard top bar spacing to accommodate native mobile controls */
        [data-testid="stHeader"] {
            background-color: transparent !important;
        }
        
        /* Remove all custom button overrides so the native toggle functions normally */
        [data-testid="stSidebarCollapseButton"] {
            margin-top: 0.5rem !important;
            margin-left: 0.5rem !important;
        }

        
        /* 3. DYNAMICALLY ANCHORED FROZEN TITLE AREA */
        /* This binds the title container natively inside the scrolling viewport wrapper */
        [data-testid="stMainView"] {
            display: flex;
            flex-direction: column;
        }
        
        .frozen-title-wrapper {
            position: sticky;
            top: 0;
            background-color: #0E1117; /* Matches default Streamlit dark mode bg */
            z-index: 99;
            padding-top: 1rem;
            padding-bottom: 0.8rem;
            border-bottom: 1px solid #31333F;
            width: 100%;
        }
        
        /* 4. Push Sidebar Elements to the absolute top */
        [data-testid="stSidebarUserContent"] {
            padding-top: 0.5rem !important;
        }
        
        /* 5. Tighten spacing layout metrics */
        hr {
            margin-top: 0.5rem !important;
            margin-bottom: 0.5rem !important;
        }
        .element-container {
            margin-bottom: 0.5rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# 1. LINK TO YOUR PUBLISHED GOOGLE SHEET CSV
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQCJHW5XPCCYbVS-_u1vmk13pGAMeVXN6xvXtPLtUWvx11Ga-9n2ViJ530xUUaFfLHt-VI6L4nLcMVl/pub?output=csv"

@st.cache_data(ttl=5)  # Refresh cache every 5 seconds so updates feel instant
def load_data():
    try:
        df = pd.read_csv(GOOGLE_SHEET_CSV_URL)
        df.columns = df.columns.str.strip()
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.strip()
        return df
    except Exception as e:
        st.error(f"Error connecting to master database: {e}")
        return pd.DataFrame()



# Helper function to convert raw seconds to a readable HH:MM:SS or MM:SS string
def format_time(seconds):
    if pd.isna(seconds) or seconds is None:
        return ""
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"






# Helper function to extract standard YouTube ID for embeds
def extract_youtube_id(url):
    if not isinstance(url, str):
        return None
    pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

# Load dynamic data
video_data = load_data()

if not video_data.empty:
    # Filter out hidden rows safely
    hide_conditions = ['hide', 'Hide']
    visible_data = video_data[
        ~video_data.get('hide', pd.Series('show', index=video_data.index)).isin(hide_conditions) & 
        ~video_data.get('display', pd.Series('show', index=video_data.index)).isin(hide_conditions) & 
        ~video_data.get('visibility', pd.Series('show', index=video_data.index)).isin(hide_conditions)
    ].copy()
    


    # 📌 RENDER FROZEN STICKY HEADER (Stays on screen when users scroll down results)
    st.markdown("""
        <div class="frozen-title">
            <h1 style="margin:0; padding: 10px 0px 0px 5px; font-size: 1.5rem;">📺 Korean Video Clips</h1>
            <p style="margin:0; padding: 0px 0px 0px 5px; font-size: 0.95rem; color: #a3a8b4;">A collaborative, AI-assisted language video archive.</p>
        </div>
    """, unsafe_allow_html=True)


    # --- SIDEBAR NAVIGATION ---
    st.sidebar.header("Filter Material")
    
    # 1. Level Dropdown Selection Window
    if 'level' in visible_data.columns:
        unique_levels = visible_data['level'].dropna().unique().tolist()
        unique_levels = [str(x).strip() for x in unique_levels if str(x).strip()]
        unique_levels.sort()
        selected_level = st.sidebar.selectbox("Select Proficiency Level", ["-- Choose a Level --"] + unique_levels)
    else:
        selected_level = "-- Choose a Level --"
        st.sidebar.warning("Add a 'level' column to your Google Sheet to filter by proficiency.")

    # Reset lower-tier configurations to default strings initially
    selected_lesson = "-- Choose a Lesson --"
    selected_grammar = "-- Choose Grammar --"

    # 2. Sequential Validation Chain (Shows ONLY the immediate next warning)
    if selected_level == "-- Choose a Level --":
        st.sidebar.info("Select a proficiency level first.")
        
    elif selected_level != "-- Choose a Level --":
        level_filtered = visible_data[visible_data['level'].astype(str).str.strip() == selected_level]
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
        
        if selected_lesson == "-- Choose a Lesson --":
            st.sidebar.info("Select a lesson to see grammar patterns.")
            
        elif selected_lesson != "-- Choose a Lesson --":
            lesson_filtered = level_filtered[level_filtered['lesson'].astype(str).str.strip() == selected_lesson]
            unique_grammar = lesson_filtered['grammar_point'].dropna().unique().tolist()
            unique_grammar = [str(x).strip() for x in unique_grammar if str(x).strip()]
            unique_grammar.sort()
            
            selected_grammar = st.sidebar.selectbox("Select Grammar Point", ["-- Choose Grammar --"] + unique_grammar)

    # --- MAIN DISPLAY CONTENT WORKSPACE ---
    # We wrap everything in an HTML div class to apply our CSS "top push" padding rule safely
    st.markdown('<div class="main-content-wrapper">', unsafe_allow_html=True)

    if selected_level != "-- Choose a Level --" and selected_lesson != "-- Choose a Lesson --" and selected_grammar != "-- Choose Grammar --":
        final_filtered = visible_data[
            (visible_data['level'].astype(str).str.strip() == selected_level) &
            (visible_data['lesson'].astype(str).str.strip() == selected_lesson) & 
            (visible_data['grammar_point'].astype(str).str.strip() == selected_grammar)
        ]
        
        st.markdown(
        f'<p style="font-size: 24px; font-weight: 600; margin-bottom: 10px;">'
        f'Title: {selected_level}, {selected_lesson}, {selected_grammar}'
        f'</p>', 
        unsafe_allow_html=True)
        st.caption(f"Found {len(final_filtered)} relevant example(s)")
        st.divider()


        for idx, row in final_filtered.iterrows():
            video_id = extract_youtube_id(row['youtube_link'])
            if video_id:
                # 1. First, parse the raw integers from the sheet data
                start_time = int(row['timestamp']) if pd.notna(row['timestamp']) else 0
                end_time = int(row['end']) if pd.notna(row['end']) and int(row['end']) > start_time else None
                
                # 2. DEFINED HERE: Convert raw seconds to human-readable strings (HH:MM:SS)
                start_formatted = format_time(start_time)
                end_formatted = format_time(end_time) if end_time else None
                
                # 3. Build the privacy-enhanced looping embed URL
                embed_url = f"https://www.youtube-nocookie.com/embed/{video_id}?start={start_time}&rel=0&modestbranding=1"
                if end_time:
                    embed_url += f"&end={end_time}"
                
                # 4. State key management for the manual replay reset system
                state_key = f"replay_{video_id}_{idx}"
                if state_key not in st.session_state:
                    st.session_state[state_key] = 0

                # 5. Render layout container safely
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
                        # This line will now read start_formatted perfectly!
                        time_display = f"`{start_formatted}`" + (f" to `{end_formatted}`" if end_formatted else "")
                        st.markdown(f"**📍Timestamp:** {time_display}")
                        
                        # 🔄 The Replay Button
                        if st.button("🔁 Replay Clip", key=f"btn_{video_id}_{idx}"):
                            st.session_state[state_key] += 1
                            st.rerun()
                        
                        # Interactive Transcripts (Accordion layout)
                        if pd.notna(row['korean_text']) and str(row['korean_text']).strip() != "":
                            with st.expander("Show Korean Transcript", expanded=False):
                                st.write(row['korean_text'])
                                
                        if pd.notna(row['english_text']) and str(row['english_text']).strip() != "":
                            with st.expander("Show English Translation", expanded=False):
                                st.write(row['english_text'])
                                
                st.markdown("---")





                                
              
            else:
                st.info("💡 Please refine your selection in the left sidebar menu to populate video clips.")
                
                st.markdown('</div>', unsafe_allow_html=True) # Closes the main-content-wrapper

