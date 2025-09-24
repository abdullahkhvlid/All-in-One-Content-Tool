import sys
import os
from gtts import gTTS
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime

# Import the content generator
from content_generator import ContentGenerator, save_generated_content, create_blog_pipeline

# Import the video generator (Stability only)
from video_generator import StabilityVideoGenerator

# Configure page
st.set_page_config(page_title="All-in-One Content Dashboard", layout="wide", page_icon="")
st.title("All-in-One Content Tool")

# Your API keys
GEMINI_API_KEY = "Your API KEY"
STABILITY_API_KEY = "Your API KEY"

# Session state initialization
if "video_history" not in st.session_state:
    st.session_state.video_history = []

# Enhanced TechCrunch Scraping Function
@st.cache_data(ttl=300)
def scrape_techcrunch(search_term="technology", max_articles=10):
    try:
        url = f"https://techcrunch.com/?s={search_term.replace(' ', '+')}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        articles = []
        article_containers = soup.find_all("div", class_="loop-card__content")
        if not article_containers:
            article_containers = soup.find_all("article") or soup.find_all("div", class_="post-block")
        for container in article_containers[:max_articles]:
            article_data = extract_article_data(container)
            if article_data["title"] and article_data["title"] != "No Title":
                articles.append(article_data)
        return articles
    except Exception as e:
        st.error(f"Scraping error: {str(e)}")
        return []

def extract_article_data(container):
    article = {
        "title": "No Title",
        "link": "#",
        "author": "",
        "date": "",
        "image": "",
        "excerpt": ""
    }
    try:
        title_selectors = [
            "h3.loop-card__title",
            "h2.loop-card__title", 
            "h3",
            "h2",
            ".post-title",
            ".entry-title"
        ]
        for selector in title_selectors:
            title_element = container.select_one(selector)
            if title_element:
                article["title"] = title_element.get_text(strip=True)
                break
        link_element = container.find("a")
        if link_element and "href" in link_element.attrs:
            link = link_element["href"]
            if link.startswith("/"):
                link = "https://techcrunch.com" + link
            article["link"] = link
        author_selectors = [
            "a.loop-card__author",
            ".author",
            ".byline",
            "[class*='author']"
        ]
        for selector in author_selectors:
            author_element = container.select_one(selector)
            if author_element:
                article["author"] = author_element.get_text(strip=True)
                break
        date_selectors = [
            ".loop-card__meta",
            ".post-date",
            ".date",
            "time",
            "[class*='date']"
        ]
        for selector in date_selectors:
            date_element = container.select_one(selector)
            if date_element:
                article["date"] = date_element.get_text(strip=True)
                break
        image_selectors = [
            "figure.loop-card__figure img",
            "img",
            ".featured-image img"
        ]
        for selector in image_selectors:
            img_element = container.select_one(selector)
            if img_element and "src" in img_element.attrs:
                article["image"] = img_element["src"]
                break
        if not article["image"]:
            prev_element = container.find_previous("figure", class_="loop-card__figure")
            if prev_element:
                img = prev_element.find("img")
                if img and "src" in img.attrs:
                    article["image"] = img["src"]
        excerpt_selectors = [
            ".loop-card__excerpt",
            ".excerpt",
            ".post-excerpt",
            "p"
        ]
        for selector in excerpt_selectors:
            excerpt_element = container.select_one(selector)
            if excerpt_element:
                excerpt_text = excerpt_element.get_text(strip=True)
                if len(excerpt_text) > 20:
                    article["excerpt"] = excerpt_text[:200] + "..." if len(excerpt_text) > 200 else excerpt_text
                    break
    except Exception as e:
        pass
    return article

def video_generation_module():
    st.header("AI Video Generation")
    st.subheader("Powered by Stability AI (Stable Video Diffusion)")

    @st.cache_resource
    def get_stability_gen():
        return StabilityVideoGenerator(STABILITY_API_KEY)
    generator = get_stability_gen()

    # Sidebar for video generation options
    with st.sidebar:
        st.subheader("🎬 Video Generation Settings")
        steps = st.slider("Sampling Steps:", 10, 50, 25)
        fps = st.slider("FPS:", 5, 12, 7)
        width = st.selectbox("Width:", [576, 1024, 768], index=0)
        height = st.selectbox("Height:", [1024, 576, 768], index=0)
        cfg_scale = st.slider("CFG Scale:", 1, 10, 2)
        motion_bucket_id = st.slider("Motion Bucket ID:", 1, 255, 127)
        cond_aug = st.number_input("Condition Augmentation (cond_aug):", min_value=0.0, max_value=1.0, value=0.02, step=0.01)
        seed = st.number_input("Seed (0 for random):", min_value=0, max_value=999999, value=0)

    prompt_templates = {
        "Nature Scene": "A serene mountain landscape at sunrise with misty clouds rolling over peaks, golden light illuminating pine trees",
        "Urban Cityscape": "A bustling modern city at night with neon lights, moving traffic streams, and tall skyscrapers",
        "Ocean Waves": "Peaceful ocean waves gently crashing on a sandy beach during golden hour, seagulls flying overhead",
        "Space Scene": "A spacecraft traveling through a nebula with colorful cosmic clouds and distant stars twinkling",
        "Abstract Art": "Flowing liquid colors mixing and swirling in slow motion, creating beautiful abstract patterns",
        "Product Demo": "A sleek smartphone floating and rotating in space with elegant lighting and particle effects",
        "Scientific": "Microscopic view of cells dividing and growing, with DNA strands visible in the background",
        "Fantasy": "A magical forest with glowing fireflies, ethereal mist, and mystical creatures moving through trees"
    }

    col1, col2 = st.columns([3, 1])
    with col1:
        selected_template = st.selectbox(
            "Choose a template or write custom prompt:",
            ["Custom Prompt"] + list(prompt_templates.keys()))
    with col2:
        if st.button("Random Template"):
            import random
            random_template = random.choice(list(prompt_templates.keys()))
            st.session_state['selected_template'] = random_template
            st.rerun()
    if 'selected_template' in st.session_state:
        selected_template = st.session_state['selected_template']
        del st.session_state['selected_template']
    if selected_template == "Custom Prompt":
        prompt = st.text_area(
            "Enter your video prompt:",
            placeholder="Describe the video you want to generate in detail...",
            height=150,
            help="Be specific about scenes, lighting, movement, and style for best results"
        )
    else:
        prompt = st.text_area(
            "Video prompt (you can edit this):",
            value=prompt_templates[selected_template],
            height=150,
            help="Feel free to modify this template or use it as-is"
        )

    with st.expander("Advanced Settings"):
        col1, col2 = st.columns(2)
        with col1:
            add_camera_movement = st.checkbox("Add camera movement", value=True)
            add_lighting_effects = st.checkbox("Enhanced lighting", value=True)
        with col2:
            add_particle_effects = st.checkbox("Add particle effects", value=False)
            dramatic_style = st.checkbox("Dramatic style", value=False)
        if add_camera_movement:
            prompt += " with smooth camera movements"
        if add_lighting_effects:
            prompt += " with cinematic lighting"
        if add_particle_effects:
            prompt += " with magical particle effects"
        if dramatic_style:
            prompt += " in dramatic cinematic style"

    if st.button("Generate Video", type="primary", disabled=not prompt):
        if not prompt.strip():
            st.error("Please enter a video prompt!")
        else:
            st.info(f"""
            **Generation Settings:**
            - **Sampling Steps:** {steps}
            - **FPS:** {fps}
            - **Width:** {width}
            - **Height:** {height}
            - **CFG Scale:** {cfg_scale}
            - **Motion Bucket ID:** {motion_bucket_id}
            - **Condition Augmentation:** {cond_aug}
            - **Seed:** {seed}
            """)
            progress_bar = st.progress(0)
            status_text = st.empty()
            with st.spinner(f"Generating your video..."):
                status_text.text(f"Sending request to Stability AI...")
                progress_bar.progress(20)
                result = generator.generate_video(
                    prompt=prompt,
                    steps=steps,
                    fps=fps,
                    width=width,
                    height=height,
                    cfg_scale=cfg_scale,
                    motion_bucket_id=motion_bucket_id,
                    cond_aug=cond_aug,
                    seed=seed if seed != 0 else None
                )
                progress_bar.progress(40)
                if result and result.get("success"):
                    status_text.text("Video generated successfully!")
                    progress_bar.progress(100)
                    st.success("Video generation completed!")
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.subheader("Generated Video")
                        if result.get("local_path") and os.path.exists(result["local_path"]):
                            st.video(result["local_path"])
                        else:
                            st.info("Video file not found locally, but generation was successful.")
                    with col2:
                        st.subheader("Generation Details")
                        st.json({
                            "Prompt": result["prompt"][:100] + "..." if len(result["prompt"]) > 100 else result["prompt"],
                            "Generated At": result["generated_at"],
                            "Parameters": result["parameters"]
                        })
                    if result.get("local_path") and os.path.exists(result["local_path"]):
                        with open(result["local_path"], "rb") as file:
                            st.download_button(
                                "Download Video",
                                file.read(),
                                file_name=os.path.basename(result["local_path"]),
                                mime="video/mp4"
                            )
                    if "video_history" not in st.session_state:
                        st.session_state.video_history = []
                    st.session_state.video_history.append(result)
                else:
                    progress_bar.progress(100)
                    status_text.text("Generation failed")
                    st.error(f"Video generation failed: {result.get('error', 'Unknown error')}")
                    with st.expander("Troubleshooting Tips"):
                        st.markdown("""
                        **Common Issues:**
                        - Check your internet connection
                        - Verify API key is correct
                        - Try a simpler prompt
                        - Check API rate limits
                        - Try again later (Stability's free tier may be busy)
                        """)
    if "video_history" in st.session_state and st.session_state.video_history:
        st.markdown("---")
        st.subheader("Generation History")
        for i, video_record in enumerate(reversed(st.session_state.video_history[-5:])):
            with st.expander(f"Video {len(st.session_state.video_history) - i}: {video_record['prompt'][:50]}..."):
                col1, col2 = st.columns([2, 1])
                with col1:
                    if video_record.get("local_path") and os.path.exists(video_record["local_path"]):
                        st.video(video_record["local_path"])
                    else:
                        st.info("Video file not available")
                with col2:
                    st.write("**Prompt:**", video_record["prompt"])
                    st.write("**Generated:**", video_record["generated_at"])
                    if video_record.get("local_path") and os.path.exists(video_record["local_path"]):
                        with open(video_record["local_path"], "rb") as file:
                            st.download_button(
                                "Download",
                                file.read(),
                                file_name=os.path.basename(video_record["local_path"]),
                                mime="video/mp4",
                                key=f"download_history_{i}"
                            )

def content_expansion_module():
    st.header("Content Generation & Expansion")
    st.subheader("Powered by Google Gemini Pro API")

    @st.cache_resource
    def get_content_generator():
        return ContentGenerator(GEMINI_API_KEY)
    generator = get_content_generator()

    with st.sidebar:
        st.subheader("Content Generation Options")
        generation_mode = st.selectbox(
            "Choose Generation Mode:",
            ["Single Content", "Multiple Variations", "Content Enhancement", "Blog Pipeline"]
        )

    if generation_mode == "Single Content":
        st.subheader("Single Content Generation")
        with st.form("single_content_form"):
            topic = st.text_area(
                "Enter your topic or prompt:",
                placeholder="e.g., The Future of Artificial Intelligence in Healthcare",
                height=100
            )
            col1, col2 = st.columns(2)
            with col1:
                content_type = st.selectbox(
                    "Content Type:",
                    ["blog", "article", "essay", "guide", "tutorial", "review"]
                )
                target_length = st.slider("Target Word Count:", 500, 5000, 2000, 100)
            with col2:
                style = st.selectbox(
                    "Writing Style:",
                    ["professional", "casual", "academic", "conversational", "technical"]
                )
            submitted = st.form_submit_button("Generate Content")
        if submitted and topic:
            with st.spinner("Generating content... This may take a few moments."):
                content = generator.generate_expanded_content(
                    topic=topic,
                    content_type=content_type,
                    target_length=target_length,
                    style=style
                )
                if content:
                    st.success(f"Generated {len(content.split())} words!")
                    with st.expander("Generated Content", expanded=True):
                        st.markdown(content)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            "Download as Text",
                            content,
                            file_name=f"{topic[:30]}_content.txt",
                            mime="text/plain"
                        )
                    with col2:
                        if st.button("Save to Outputs"):
                            content_data = {
                                "topic": topic,
                                "content_type": content_type,
                                "style": style,
                                "target_length": target_length,
                                "content": content,
                                "word_count": len(content.split()),
                                "generated_at": datetime.now().isoformat()
                            }
                            filepath = save_generated_content(content_data)
                            st.success(f"Content saved to: {filepath}")

    elif generation_mode == "Multiple Variations":
        st.subheader("Multiple Content Variations")
        with st.form("multiple_variations_form"):
            topic = st.text_area(
                "Enter your topic:",
                placeholder="e.g., Benefits of Remote Work",
                height=100
            )
            col1, col2 = st.columns(2)
            with col1:
                variation_count = st.slider("Number of Variations:", 2, 5, 3)
            with col2:
                target_length = st.slider("Target Word Count per Variation:", 1000, 3000, 2000, 100)
            submitted = st.form_submit_button("Generate Variations")
        if submitted and topic:
            with st.spinner(f"Generating {variation_count} variations..."):
                variations = generator.generate_multiple_variations(
                    topic=topic,
                    count=variation_count,
                    target_length=target_length
                )
                if variations:
                    st.success(f"Generated {len(variations)} variations!")
                    tab_names = [f"Variation {i+1} ({v['style'].title()})" for i, v in enumerate(variations)]
                    tabs = st.tabs(tab_names)
                    for i, (tab, variation) in enumerate(zip(tabs, variations)):
                        with tab:
                            st.info(f"Style: {variation['style'].title()} | Words: {variation['word_count']}")
                            st.markdown(variation['content'])
                            st.download_button(
                                f"Download Variation {i+1}",
                                variation['content'],
                                file_name=f"{topic[:30]}_variation_{i+1}.txt",
                                mime="text/plain",
                                key=f"download_var_{i}"
                            )
                    if st.button("Save All Variations"):
                        all_variations_data = {
                            "topic": topic,
                            "variations": variations,
                            "total_variations": len(variations),
                            "generated_at": datetime.now().isoformat()
                        }
                        filepath = save_generated_content(all_variations_data, f"variations_{topic[:20]}.json")
                        st.success(f"All variations saved to: {filepath}")

    elif generation_mode == "Content Enhancement":
        st.subheader("Content Enhancement")
        with st.form("content_enhancement_form"):
            original_content = st.text_area(
                "Paste your existing content:",
                placeholder="Enter the content you want to enhance...",
                height=200
            )
            enhancement_type = st.selectbox(
                "Enhancement Type:",
                ["expand", "rewrite", "improve", "summarize"],
                format_func=lambda x: {
                    "expand": "Expand Content (add detail & length)",
                    "rewrite": "Rewrite Content (same info, different style)",
                    "improve": "Improve Content (fix & enhance)",
                    "summarize": "Summarize Content (condense key points)"
                }[x]
            )
            submitted = st.form_submit_button("Enhance Content")
        if submitted and original_content:
            with st.spinner("Enhancing content..."):
                enhanced_content = generator.enhance_existing_content(
                    original_content=original_content,
                    enhancement_type=enhancement_type
                )
                if enhanced_content:
                    st.success("Content enhanced successfully!")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Original Content")
                        st.text_area("", original_content, height=300, disabled=True, key="original")
                        st.caption(f"Word count: {len(original_content.split())}")
                    with col2:
                        st.subheader("Enhanced Content")
                        st.text_area("", enhanced_content, height=300, disabled=True, key="enhanced")
                        st.caption(f"Word count: {len(enhanced_content.split())}")
                    st.download_button(
                        "Download Enhanced Content",
                        enhanced_content,
                        file_name=f"enhanced_content_{enhancement_type}.txt",
                        mime="text/plain"
                    )

    elif generation_mode == "Blog Pipeline":
        st.subheader("Complete Blog Creation Pipeline")
        st.info("Generate a complete blog package including content, SEO meta description, and social media snippets.")
        with st.form("blog_pipeline_form"):
            topic = st.text_area(
                "Enter your blog topic:",
                placeholder="e.g., 10 Essential Tips for Digital Marketing Success",
                height=100
            )
            submitted = st.form_submit_button("Create Complete Blog Package")
        if submitted and topic:
            with st.spinner("Creating complete blog package..."):
                blog_package = create_blog_pipeline(topic, generator)
                if blog_package:
                    st.success("Blog package created successfully!")
                    with st.expander("Main Blog Content", expanded=True):
                        st.markdown(blog_package['main_content'])
                        st.caption(f"Word count: {blog_package['word_count']}")
                    with st.expander("SEO Meta Description"):
                        st.text_area("Meta Description:", blog_package['meta_description'], height=100, disabled=True)
                    with st.expander("Social Media Snippets"):
                        st.markdown(blog_package['social_media_content'])
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.download_button(
                            "Download Blog Content",
                            blog_package['main_content'],
                            file_name=f"{topic[:30]}_blog.txt",
                            mime="text/plain"
                        )
                    with col2:
                        st.download_button(
                            "Download Complete Package",
                            json.dumps(blog_package, indent=2),
                            file_name=f"{topic[:30]}_complete_package.json",
                            mime="application/json"
                        )
                    with col3:
                        if st.button("Save to Outputs"):
                            filepath = save_generated_content(blog_package, f"blog_package_{topic[:20]}.json")
                            st.success(f"Blog package saved to: {filepath}")

    with st.sidebar:
        st.markdown("---")
        st.subheader("Usage Info")
        st.info("""
        **API Used:** Google Gemini Pro (Free Tier)
        **Features:**
        - Single content generation
        - Multiple variations
        - Content enhancement
        - Complete blog pipeline
        **Output:** Up to 2000+ words per generation
        """)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Job Scraping", "Video Generation", "Text-to-Speech", "Media Output", "Content Expansion", "Project Info"
])

with tab1:
    st.header("News Scraper")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_categories = {
            "Fast News & SNS Data": "breaking news social media trending",
            "Marketing-Focused Content": "marketing advertising digital marketing content strategy",
            "AI & Machine Learning": "artificial intelligence",
            "Startups & Funding": "startup funding",
            "Mobile Technology": "mobile technology",
            "Cybersecurity": "cybersecurity",
            "Space Technology": "space technology",
            "Health Tech": "health technology",
            "Custom Search": "custom"
        }
        selected_category = st.selectbox("Choose Category:", list(search_categories.keys()))
    with col2:
        max_articles = st.slider("Max Articles:", 5, 20, 10)
    with col3:
        if st.button("Refresh", type="primary"):
            st.cache_data.clear()
    if search_categories[selected_category] == "custom":
        user_query = st.text_input("Enter custom search term:", placeholder="e.g., blockchain, fintech")
        search_term = user_query if user_query else "technology"
    else:
        search_term = search_categories[selected_category]
        st.info(f"Searching for: **{search_term}**")
    if search_term:
        with st.spinner(f"Scraping TechCrunch for '{search_term}'..."):
            default_articles = scrape_techcrunch(search_term, max_articles)
        if default_articles:
            st.success(f"Found {len(default_articles)} articles")
            st.subheader(f"Latest Articles - {selected_category}")
            df_articles = pd.DataFrame(default_articles)
            view_mode = st.radio("View Mode:", ["Table View", "Card View"], horizontal=True)
            if view_mode == "Table View":
                display_df = df_articles[['title', 'author', 'date', 'excerpt']].copy()
                display_df.columns = ['Title', 'Author', 'Date', 'Excerpt']
                st.dataframe(display_df, use_container_width=True, height=400)
            else:
                for i, article in enumerate(default_articles):
                    with st.container():
                        col_img, col_content = st.columns([1, 3])
                        with col_img:
                            if article["image"]:
                                try:
                                    st.image(article["image"], use_container_width=True)
                                except:
                                    st.write("No image")
                            else:
                                st.write("No image")
                        with col_content:
                            if article["link"] != "#":
                                st.markdown(f"### [{article['title']}]({article['link']})")
                            else:
                                st.markdown(f"### {article['title']}")
                            if article["author"] or article["date"]:
                                meta_info = []
                                if article["author"]:
                                    meta_info.append(f"{article['author']}")
                                if article["date"]:
                                    meta_info.append(f"{article['date']}")
                                st.caption(" | ".join(meta_info))
                            if article["excerpt"]:
                                st.write(article["excerpt"])
                            if article["link"] != "#":
                                st.markdown(f"[Read Full Article]({article['link']})")
                        st.markdown("---")
            st.subheader("Download Data")
            csv_data = df_articles.to_csv(index=False)
            st.download_button(
                "Download Articles CSV",
                csv_data,
                file_name=f"techcrunch_articles_{search_term.replace(' ', '_')}.csv",
                mime="text/csv"
            )
        else:
            st.warning(f"No articles found for '{search_term}'. Try a different search term.")
            st.info("**Suggestions:** Try broader terms like 'AI', 'startup', 'tech'")
    else:
        st.info("Please select a category or enter a search term to start scraping!")

with tab2:
    video_generation_module()

with tab3:
    st.header("Text-to-Speech (TTS)")
    st.info("Convert any text to speech using Google's TTS API")
    
    # Input text
    tts_text = st.text_area(
        "Enter text to convert to speech:",
        placeholder="Type something like: Hello, this is a test",
        height=150
    )
    
    # Language selection
    lang = st.selectbox(
        "Select language",
        ["en", "hi", "ur"],  # English, Hindi, Urdu
        format_func=lambda x: {
            "en": "English",
            "hi": "Hindi",
            "ur": "Urdu"
        }[x]
    )
    
    if st.button("Generate Audio", type="primary"):
        if tts_text.strip():
            with st.spinner("Generating audio..."):
                try:
                    # Generate audio
                    tts = gTTS(text=tts_text, lang=lang)
                    tts.save("tts_output.mp3")
                    
                    # Play and download
                    st.audio("tts_output.mp3", format="audio/mp3")
                    st.success("Audio generated successfully!")
                    
                    with open("tts_output.mp3", "rb") as f:
                        st.download_button(
                            "Download Audio",
                            f,
                            file_name="tts_output.mp3",
                            mime="audio/mpeg"
                        )
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter some text first!")

with tab4:
    st.header("Media Output")
    video_dir = os.path.join(os.path.dirname(__file__), "..", "media", "outputs")
    video_dir = os.path.abspath(video_dir)
    if os.path.exists(video_dir) and os.path.isdir(video_dir):
        videos = [f for f in os.listdir(video_dir) if f.endswith((".mp4", ".avi", ".mov"))]
        audio_files = [f for f in os.listdir(video_dir) if f.endswith((".mp3", ".wav", ".m4a"))]
        if videos or audio_files:
            if videos:
                st.subheader("Generated Videos")
                for vid in videos:
                    video_path = os.path.join(video_dir, vid)
                    st.video(video_path)
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.caption(f"{vid}")
                    with col2:
                        try:
                            file_size = os.path.getsize(video_path)
                            size_mb = file_size / (1024 * 1024)
                            st.caption(f"{size_mb:.1f} MB")
                        except:
                            st.caption("Size unknown")
                    with col3:
                        try:
                            with open(video_path, "rb") as file:
                                st.download_button(
                                    "📥",
                                    file.read(),
                                    file_name=vid,
                                    mime="video/mp4",
                                    key=f"download_{vid}",
                                    help="Download video"
                                )
                        except:
                            pass
            if audio_files:
                st.subheader("🎵 Generated Audio")
                for audio in audio_files:
                    audio_path = os.path.join(video_dir, audio)
                    st.audio(audio_path)
                    st.caption(f"{audio}")
                    try:
                        with open(audio_path, "rb") as file:
                            st.download_button(
                                "Download Audio",
                                file.read(),
                                file_name=audio,
                                mime="audio/mpeg",
                                key=f"download_audio_{audio}"
                            )
                    except:
                        pass
        else:
            st.info("No media files found in media/outputs.")
            st.markdown("""
            **Generate some videos first!**
            
            Go to the **Video Generation** tab to create AI-generated videos using Stability AI.
            Generated videos will appear here automatically.
            """)
    else:
        st.info("The media/outputs directory does not exist yet.")
        if st.button("Create Media Directory"):
            try:
                os.makedirs(video_dir, exist_ok=True)
                st.success("Media directory created!")
                st.rerun()
            except Exception as e:
                st.error(f"Error creating directory: {e}")

with tab5:
    content_expansion_module()

with tab6:
    st.header("Project Information")
    st.markdown("""
    ## All-in-One Content Tool

    ### Features Overview:

    #### **Active Features:**
    - **Fast News & SNS Data**: Real-time breaking news and social media trends
    - *Marketing-Focused Content**: Marketing, advertising, and content strategy articles
    - **TechCrunch Scraping**: Enhanced web scraping with multiple categories
    - **Data Export**: CSV download functionality
    - **Responsive UI**: Modern Streamlit interface with tabs and cards
    - **Caching**: Optimized performance with data caching
    - **Content Expansion**: AI-powered content generation using Gemini API
    - **Multiple Variations**: Generate 5x 2000+ word variations
    - **Content Enhancement**: Expand, rewrite, improve existing content
    - **Blog Pipeline**: Complete blog packages with SEO and social media
    - **Video Generation**: AI-powered video creation using Stability AI
    - **Media Management**: Video playback and download functionality

    #### **Planned Features:**
    - **Text-to-Speech**: Voice synthesis capabilities (placeholder)
    - **Video-to-Blog**: Convert videos to blog content
    - **Social Media Automation**: Auto-posting capabilities

    ### **Technical Stack:**
    - **Frontend**: Streamlit
    - **Web Scraping**: BeautifulSoup + Requests
    - **Data Processing**: Pandas
    - **AI Content Generation**: Google Gemini Pro API
    - **AI Video Generation**: Stability AI API
    - **Caching**: Streamlit cache system

    ### **Project Structure:**
    ```
    project/
    ├── app.py                 # Main dashboard
    ├── content_generator.py   # AI content generation
    ├── video_generator.py     # Stability AI video generation
    ├── scraping/
    │   └── content_scraper.py # Scraping modules
    ├── media/
    │   └── outputs/          # Generated media files
    ├── outputs/              # Generated content files
    └── requirements.txt       # Dependencies
    ```

    ### **API Configuration:**
    - **Gemini API**: Content generation and text processing
    - **Stability AI API**: Video generation (Stable Video Diffusion)
    - **TechCrunch Scraping**: Real-time news and article extraction

    ### **Video Generation Features:**
    """)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Video Styles", "default")
    with col2:
        st.metric("Max Duration", "~4s")
    with col3:
        st.metric("Aspect Ratios", "4")
    with col4:
        st.metric("Quality Levels", "default")
    st.markdown("---")
    st.subheader("API Status")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ** Gemini API**
        - Status:  Active
        - Purpose: Content Generation
        - Features: Text expansion, blog creation
        """)
    with col2:
        st.markdown("""
        ** Stability AI API**
        - Status:  Active
        - Purpose: Video Generation
        - Features: Stable Video Diffusion (SVD)
        """)
    with st.expander("Usage Tips & Best Practices"):
        st.markdown("""
        ### Video Generation Tips:
        - **Be Specific**: Include details about lighting, movement, and style
        - **Optimal Length**: SVD outputs ~4s videos
        - **Prompt**: Avoid copyrighted/trademarked characters

        ### Content Generation Tips:
        - **Target Length**: 2000+ words for comprehensive articles
        - **Style Consistency**: Choose one style and stick with it
        - **Enhancement Types**: Use 'expand' for more detail, 'improve' for quality

        ### Scraping Tips:
        - **Broad Terms**: Use general keywords like 'AI', 'startup', 'tech'
        - **Refresh Data**: Click refresh to get latest articles
        - **Export Options**: Download CSV for further analysis
        """)
    st.markdown("---")
    st.markdown("""
    ** Built with ❤️ using Streamlit | Enhanced with Gemini AI + Stability AI**
    *Total Features: Job Scraping + Content Generation + Video Generation + Media Management*

    """)
