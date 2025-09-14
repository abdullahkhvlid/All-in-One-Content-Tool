import google.generativeai as genai
import streamlit as st
import time
import json
from datetime import datetime
import os

class ContentGenerator:
    def __init__(self, api_key):
        """Initialize the Gemini API client"""
        genai.configure(api_key=api_key)
        # Updated model name - the old 'gemini-pro' is deprecated
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    def generate_expanded_content(self, topic, content_type="blog", target_length=2000, style="professional"):
        """
        Generate expanded content using Gemini API
        
        Args:
            topic (str): The main topic or prompt
            content_type (str): Type of content (blog, article, essay, etc.)
            target_length (int): Target word count
            style (str): Writing style (professional, casual, academic, etc.)
        """
        
        # Create a detailed prompt for content generation
        prompt = f"""
        Create a comprehensive {content_type} post about: {topic}
        
        Requirements:
        - Target length: approximately {target_length} words
        - Writing style: {style}
        - Include an engaging introduction
        - Organize content with clear headings and subheadings
        - Provide detailed explanations and examples
        - Include a compelling conclusion
        - Make it SEO-friendly with natural keyword integration
        
        Structure the content with proper formatting using markdown.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            st.error(f"Error generating content: {str(e)}")
            return None
    
    def generate_multiple_variations(self, topic, count=5, target_length=2000):
        """Generate multiple variations of content for the same topic"""
        variations = []
        
        for i in range(count):
            st.write(f"Generating variation {i+1}/{count}...")
            
            # Different styles for each variation
            styles = ["professional", "casual", "academic", "conversational", "technical"]
            style = styles[i % len(styles)]
            
            prompt = f"""
            Create a unique {target_length}-word article about: {topic}
            
            Style: {style}
            Variation: #{i+1}
            
            Make this version distinct from other articles on the same topic by:
            - Taking a unique angle or perspective
            - Using different examples and case studies
            - Varying the structure and flow
            - Incorporating different subtopics and details
            
            Format with markdown headings and ensure high quality, original content.
            """
            
            try:
                response = self.model.generate_content(prompt)
                variations.append({
                    'variation': i+1,
                    'style': style,
                    'content': response.text,
                    'word_count': len(response.text.split()),
                    'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                # Add delay to respect API rate limits
                time.sleep(1)
                
            except Exception as e:
                st.error(f"Error generating variation {i+1}: {str(e)}")
                continue
        
        return variations
    
    def enhance_existing_content(self, original_content, enhancement_type="expand"):
        """
        Enhance existing content by expanding, rewriting, or improving it
        
        Args:
            original_content (str): The original content to enhance
            enhancement_type (str): Type of enhancement (expand, rewrite, improve, summarize)
        """
        
        enhancement_prompts = {
            "expand": f"""
            Take the following content and expand it significantly while maintaining the original message and tone:
            
            Original Content:
            {original_content}
            
            Please:
            - Add more detailed explanations
            - Include relevant examples and case studies
            - Expand on key points with additional insights
            - Maintain the original structure but add depth
            - Target at least 2000 words in the expanded version
            """,
            
            "rewrite": f"""
            Rewrite the following content completely while keeping the same core information:
            
            Original Content:
            {original_content}
            
            Please:
            - Use different wording and sentence structures
            - Reorganize the information flow
            - Add fresh perspectives and angles
            - Maintain accuracy but change the presentation
            - Make it approximately 2000 words
            """,
            
            "improve": f"""
            Improve and enhance the following content:
            
            Original Content:
            {original_content}
            
            Please:
            - Fix any grammatical errors
            - Improve clarity and readability
            - Add missing information or context
            - Enhance the structure and flow
            - Make it more engaging and comprehensive
            """,
            
            "summarize": f"""
            Create a comprehensive summary of the following content:
            
            Original Content:
            {original_content}
            
            Please create a detailed summary that:
            - Captures all key points
            - Maintains important details
            - Is well-structured and readable
            - Is approximately 500-800 words
            """
        }
        
        prompt = enhancement_prompts.get(enhancement_type, enhancement_prompts["expand"])
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            st.error(f"Error enhancing content: {str(e)}")
            return None

def save_generated_content(content_data, filename=None):
    """Save generated content to a file"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"generated_content_{timestamp}.json"
    
    # Create outputs directory if it doesn't exist
    os.makedirs("outputs", exist_ok=True)
    
    filepath = os.path.join("outputs", filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(content_data, f, indent=2, ensure_ascii=False)
    
    return filepath

def create_blog_pipeline(topic, generator):
    """Complete blog creation pipeline"""
    st.subheader("🚀 Blog Creation Pipeline")
    
    # Step 1: Generate main content
    st.write("**Step 1:** Generating main blog content...")
    main_content = generator.generate_expanded_content(
        topic=topic,
        content_type="blog post",
        target_length=2000,
        style="professional"
    )
    
    if main_content:
        st.success("✅ Main content generated!")
        
        # Step 2: Generate SEO meta description
        st.write("**Step 2:** Generating SEO meta description...")
        meta_prompt = f"""
        Create a compelling SEO meta description (150-160 characters) for this blog post:
        Topic: {topic}
        
        Make it engaging and include relevant keywords.
        """
        
        try:
            meta_response = generator.model.generate_content(meta_prompt)
            meta_description = meta_response.text.strip()
        except:
            meta_description = f"Comprehensive guide about {topic}"
        
        # Step 3: Generate social media snippets
        st.write("**Step 3:** Generating social media snippets...")
        social_prompt = f"""
        Create 3 different social media posts to promote this blog about: {topic}
        
        1. Twitter post (280 characters max)
        2. LinkedIn post (professional tone, 1-2 paragraphs)
        3. Facebook post (engaging and casual, 1 paragraph)
        
        Each should be engaging and include relevant hashtags.
        """
        
        try:
            social_response = generator.model.generate_content(social_prompt)
            social_content = social_response.text
        except:
            social_content = "Social media content generation failed"
        
        # Compile complete blog package
        blog_package = {
            "topic": topic,
            "main_content": main_content,
            "meta_description": meta_description,
            "social_media_content": social_content,
            "word_count": len(main_content.split()),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "api_used": "Google Gemini 1.5 Flash"
        }
        
        return blog_package
    
    return None