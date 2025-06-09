"""Google Gemini AI integration for content processing."""

import asyncio
from typing import Dict, List, Optional, Any
import json
import re

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from src.config import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class GeminiClient:
    """Client for Google Gemini AI API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini client."""
        self.api_key = api_key or settings.gemini_api_key
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 8192,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        # Initialize chat session for multi-turn conversations
        self.chat_session = None
    
    async def generate_content(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate content using Gemini."""
        try:
            # Build full prompt
            full_prompt = prompt
            if context:
                full_prompt = f"{context}\n\n{prompt}"
            
            # Generate response
            response = await asyncio.to_thread(
                self.model.generate_content,
                full_prompt
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise
    
    async def structure_markdown(self, markdown_content: str, url: str, 
                               title: str = "") -> Dict[str, Any]:
        """Structure markdown content using AI."""
        prompt = f"""You are an expert at structuring and enhancing documentation for technical content.

Given the following markdown content from {url}, please:

1. Clean up and properly format the markdown
2. Organize content into logical sections
3. Add a clear structure with proper headings
4. Ensure all code blocks have language annotations
5. Create a brief summary (2-3 sentences)
6. Extract key topics and concepts
7. Identify the main purpose/category of the page

Title: {title or 'Unknown'}
URL: {url}

MARKDOWN CONTENT:
{markdown_content[:4000]}  # Limit to 4000 chars to avoid token limits

Please return a JSON response with the following structure:
{{
    "structured_markdown": "The cleaned and structured markdown content",
    "summary": "Brief 2-3 sentence summary",
    "key_topics": ["topic1", "topic2", ...],
    "page_type": "documentation|tutorial|api-reference|blog|other",
    "main_concepts": ["concept1", "concept2", ...],
    "code_languages": ["python", "javascript", ...],
    "quality_score": 0.0-1.0
}}"""

        try:
            response = await self.generate_content(prompt)
            
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
                return result
            else:
                logger.warning("No JSON found in Gemini response")
                return {
                    "structured_markdown": markdown_content,
                    "summary": "",
                    "key_topics": [],
                    "page_type": "other",
                    "main_concepts": [],
                    "code_languages": [],
                    "quality_score": 0.5
                }
                
        except Exception as e:
            logger.error(f"Failed to structure markdown: {e}")
            return {
                "structured_markdown": markdown_content,
                "summary": "",
                "key_topics": [],
                "page_type": "other", 
                "main_concepts": [],
                "code_languages": [],
                "quality_score": 0.0,
                "error": str(e)
            }
    
    async def generate_llms_txt_entry(self, page_data: Dict[str, Any]) -> str:
        """Generate llms.txt format entry for a page."""
        prompt = f"""Create a concise llms.txt style entry for this documentation page.

Page Title: {page_data.get('title', 'Unknown')}
URL: {page_data.get('url', '')}
Summary: {page_data.get('summary', '')}
Key Topics: {', '.join(page_data.get('key_topics', []))}

Content Preview:
{page_data.get('content', '')[:1000]}

Generate a structured entry in this format:
- Path: (relative URL path)
- Title: (clear, descriptive title)
- Description: (1-2 sentence description)
- Keywords: (comma-separated relevant keywords)
- Content-Type: (page type)

Keep it concise and informative for LLM consumption."""

        try:
            response = await self.generate_content(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"Failed to generate llms.txt entry: {e}")
            return f"- Path: {page_data.get('url', '')}\n- Title: {page_data.get('title', 'Unknown')}\n- Description: Page content\n- Keywords: documentation\n- Content-Type: {page_data.get('page_type', 'other')}"
    
    async def extract_code_examples(self, markdown_content: str) -> List[Dict[str, str]]:
        """Extract and annotate code examples from markdown."""
        prompt = f"""Extract all code examples from this markdown content and provide:
1. The code snippet
2. The programming language
3. A brief description of what the code does
4. Any important notes or warnings

MARKDOWN CONTENT:
{markdown_content[:3000]}

Return a JSON array of code examples:
[
    {{
        "code": "the actual code",
        "language": "python|javascript|etc",
        "description": "what this code does",
        "notes": "any important notes"
    }}
]"""

        try:
            response = await self.generate_content(prompt)
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                return json.loads(json_match.group())
            return []
        except Exception as e:
            logger.error(f"Failed to extract code examples: {e}")
            return []
    
    async def generate_content_index(self, pages: List[Dict[str, Any]]) -> str:
        """Generate a comprehensive index for multiple pages."""
        # Prepare page summaries
        page_summaries = []
        for page in pages[:20]:  # Limit to 20 pages to avoid token limits
            summary = f"- {page.get('title', 'Unknown')}: {page.get('summary', 'No summary')}"
            page_summaries.append(summary)
        
        prompt = f"""Create a comprehensive documentation index for a website with these pages:

{chr(10).join(page_summaries)}

Generate a well-structured index that:
1. Groups related pages by topic/category
2. Provides a clear hierarchy
3. Includes brief descriptions
4. Highlights the most important pages
5. Suggests a logical reading order for newcomers

Format as clean markdown with proper sections and organization."""

        try:
            response = await self.generate_content(prompt)
            return response
        except Exception as e:
            logger.error(f"Failed to generate content index: {e}")
            return "# Documentation Index\n\nError generating index"
    
    async def classify_content(self, content: str, url: str) -> Dict[str, Any]:
        """Classify content type and extract metadata."""
        prompt = f"""Analyze this web content and classify it:

URL: {url}
Content Preview: {content[:1500]}

Provide classification:
1. Content type (documentation, tutorial, api-reference, blog, landing-page, other)
2. Technical level (beginner, intermediate, advanced)
3. Primary topic/domain
4. Target audience
5. Completeness score (0.0-1.0)
6. Usefulness score (0.0-1.0)

Return as JSON."""

        try:
            response = await self.generate_content(prompt)
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
            return {}
        except Exception as e:
            logger.error(f"Failed to classify content: {e}")
            return {}


# Singleton instance
gemini_client = None


def get_gemini_client() -> GeminiClient:
    """Get or create Gemini client instance."""
    global gemini_client
    if gemini_client is None:
        gemini_client = GeminiClient()
    return gemini_client


# Convenience functions
async def structure_markdown(markdown_content: str, url: str, title: str = "") -> Dict[str, Any]:
    """Structure markdown content using AI."""
    client = get_gemini_client()
    return await client.structure_markdown(markdown_content, url, title)


async def generate_llms_txt_entry(page_data: Dict[str, Any]) -> str:
    """Generate llms.txt format entry for a page."""
    client = get_gemini_client()
    return await client.generate_llms_txt_entry(page_data)


async def extract_code_examples(markdown_content: str) -> List[Dict[str, str]]:
    """Extract code examples from markdown."""
    client = get_gemini_client()
    return await client.extract_code_examples(markdown_content)


async def generate_content_index(pages: List[Dict[str, Any]]) -> str:
    """Generate a comprehensive index for multiple pages."""
    client = get_gemini_client()
    return await client.generate_content_index(pages)