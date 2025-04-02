"""
Content Generator Module
Generates script and title content based on user's idea using OpenAI API
"""

import os
import logging
import time
import openai
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

# Content styles with prompts for different types of shorts
CONTENT_STYLES = {
    "educational": "Create a script about {idea}.",
    "entertaining": "Create a script about {idea}.",
    "storytelling": "Create a script about {idea}.",
    "tutorial": "Create a script about {idea}.",
    "fact_list": "Create a script about {idea}.",
    "motivational": "Create a script about {idea}."
}


def generate_content(idea, max_words=150, style="educational", retries=2, timeout=20):
    """
    Generate content for YouTube short using AI
    
    Args:
        idea (str): The user's input idea
        max_words (int): Maximum word count for the script
        style (str): Content style (educational, entertaining, etc.)
        retries (int): Number of retries if API call fails
        timeout (int): Timeout in seconds for API call
        
    Returns:
        tuple: (script, title, hook)
    """
    try:
        if not openai.api_key:
            logger.warning("OpenAI API key not found. Using sample content instead.")
            # Return sample content for testing when API key is not available
            return generate_sample_content(idea, style)
        
        logger.info(f"Generating {style} content with OpenAI for idea: {idea}")
        
        # Get style prompt or default to educational
        style_prompt = CONTENT_STYLES.get(style, CONTENT_STYLES["educational"])
        
        # Create prompt for GPT
        prompt = f"""
        {style_prompt.format(idea=idea)}
        
        The response should be concise and formatted as follows:
        
        TITLE: [attention-grabbing title]
        
        HOOK: [a 1-sentence attention-grabbing opener that will appear first]
        
        SCRIPT: [script that's naturally paced for a 30-second video, less than {max_words} words]
        
        Make the content engaging, interesting, and appropriate for a short-form vertical video.
        The tone should be conversational and designed to capture attention quickly.
        """
        
        # Attempt API call with retries
        for attempt in range(retries + 1):
            try:
                # Call OpenAI API
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": f"You are a creative content writer specializing in engaging {style} YouTube Shorts scripts."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=600,
                    temperature=0.7,
                    request_timeout=timeout
                )
                
                # Parse response
                content = response.choices[0].message.content.strip()
                
                # Extract title, hook, and script
                title_section = content.split("TITLE:")[1].split("HOOK:")[0].strip() if "HOOK:" in content else content.split("TITLE:")[1].split("SCRIPT:")[0].strip()
                hook_section = content.split("HOOK:")[1].split("SCRIPT:")[0].strip() if "HOOK:" in content else ""
                script_section = content.split("SCRIPT:")[1].strip() if "SCRIPT:" in content else content.split("TITLE:")[1].strip()
                
                # Format the script for better reading and speech
                formatted_script = format_script(script_section, hook_section)
                
                return formatted_script, title_section, hook_section
                
            except Exception as e:
                if attempt < retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"API call failed, retrying in {wait_time} seconds. Error: {str(e)}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All retry attempts failed: {str(e)}")
                    raise
    
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        # Fallback to sample content on error
        return generate_sample_content(idea, style)


def format_script(script, hook=""):
    """
    Format the script for better reading and speech
    
    Args:
        script (str): The raw script text
        hook (str): Optional hook to prepend
        
    Returns:
        str: Formatted script
    """
    # Remove excess whitespace
    script = " ".join(script.split())
    
    # Add hook at the beginning if provided
    if hook and not script.startswith(hook):
        script = f"{hook} {script}"
    
    # Break into sentences and paragraphs
    sentences = []
    current = ""
    
    for char in script:
        current += char
        if char in ['.', '!', '?'] and current.strip():
            sentences.append(current.strip())
            current = ""
    
    # Add any remaining text
    if current.strip():
        sentences.append(current.strip())
    
    # Group sentences into paragraphs (every 2-3 sentences)
    paragraphs = []
    for i in range(0, len(sentences), random.randint(1, 2)):
        paragraph = " ".join(sentences[i:i+random.randint(1, 2)])
        paragraphs.append(paragraph)
    
    # Join paragraphs with newlines
    formatted = "\n\n".join(paragraphs)
    
    return formatted


def generate_sample_content(idea, style="educational"):
    """
    Generate sample content when API is unavailable
    
    Args:
        idea (str): The user's input idea
        style (str): Content style
        
    Returns:
        tuple: (script, title, hook)
    """
    # Different content based on style
    if style == "entertaining":
        title = f"You Won't Believe These Facts About {idea.title()}!"
        hook = f"Did you know that {idea} has some mind-blowing secrets?"
        script = f"""
        Did you know these incredible facts about {idea}?
        
        First, {idea} is actually more fascinating than most people realize.
        
        Scientists have discovered that {idea} can be explained in ways that will blow your mind.
        
        If you found this interesting, like and subscribe for more amazing facts!
        """
    
    elif style == "tutorial":
        title = f"Master {idea.title()} In Under 30 Seconds!"
        hook = f"Here's how to quickly become a pro at {idea}!"
        script = f"""
        Today I'll show you how to master {idea} in just a few steps.
        
        Step 1: Start with the basics and understand the fundamentals.
        
        Step 2: Practice regularly and focus on improving gradually.
        
        Step 3: Use these pro techniques to take your skills to the next level.
        
        That's it! You now know the secrets to mastering {idea}!
        """
    
    else:  # Default educational
        title = f"Amazing Facts About {idea.title()}"
        hook = f"Here's what you never knew about {idea}!"
        script = f"""
        Did you know these incredible facts about {idea}?
        
        First, {idea} is actually more fascinating than most people realize.
        
        Scientists have discovered that {idea} can be explained in ways that will blow your mind.
        
        If you found this interesting, like and subscribe for more amazing facts!
        """
    
    return script.strip(), title, hook


if __name__ == "__main__":
    # Simple test
    test_idea = "space exploration"
    script, title, hook = generate_content(test_idea, style="entertaining")
    print(f"Title: {title}")
    print(f"Hook: {hook}")
    print(f"Script:\n{script}") 