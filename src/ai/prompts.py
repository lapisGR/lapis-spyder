"""AI prompts for content processing and structuring."""

from typing import Dict, List, Optional


class PromptTemplates:
    """Collection of prompt templates for different AI tasks."""
    
    # Content structuring prompts
    STRUCTURE_DOCUMENTATION = """You are an expert technical documentation specialist.

Given the following content from {url}, please structure it as high-quality documentation:

Title: {title}
Current Content:
{content}

Requirements:
1. Organize content with clear hierarchy (H1, H2, H3)
2. Add a table of contents if content is long
3. Ensure code blocks have proper language tags
4. Format lists and tables properly
5. Add clear section breaks
6. Improve readability while preserving all information
7. Fix any markdown formatting issues

Return the structured markdown content."""

    STRUCTURE_TUTORIAL = """You are an expert at creating clear, educational tutorials.

Given the following content from {url}, structure it as an effective tutorial:

Title: {title}
Current Content:
{content}

Requirements:
1. Add clear learning objectives at the start
2. Structure content in logical steps
3. Add explanations for complex concepts
4. Ensure code examples are complete and runnable
5. Add "Try it yourself" sections where appropriate
6. Include common pitfalls or gotchas
7. End with a summary and next steps

Return the structured tutorial in markdown format."""

    STRUCTURE_API_REFERENCE = """You are an expert at creating clear API documentation.

Given the following API content from {url}, structure it as professional API reference:

Title: {title}
Current Content:
{content}

Requirements:
1. Group endpoints by resource/functionality
2. Clearly show HTTP methods and paths
3. Document all parameters with types and descriptions
4. Include request/response examples
5. Note authentication requirements
6. Add error codes and meanings
7. Include rate limits if mentioned

Return the structured API reference in markdown format."""

    # Content extraction prompts
    EXTRACT_KEY_INFORMATION = """Extract the most important information from this content:

URL: {url}
Content:
{content}

Please identify:
1. Main purpose/goal of the page
2. Key concepts explained (list up to 10)
3. Technologies/tools mentioned
4. Prerequisites or dependencies
5. Action items or steps to follow
6. Important warnings or notes
7. Related resources or links

Format as structured JSON."""

    EXTRACT_CODE_PATTERNS = """Analyze the code examples in this content and identify patterns:

Content:
{content}

For each code example, identify:
1. Programming language
2. Purpose/functionality
3. Design patterns used
4. Best practices demonstrated
5. Potential improvements

Return as JSON array."""

    # Index generation prompts
    GENERATE_LLMS_TXT = """Generate a llms.txt format entry for this documentation page.

Page Data:
- URL: {url}
- Title: {title}
- Summary: {summary}
- Type: {page_type}
- Topics: {topics}

Create a concise, structured entry following the llms.txt specification:
- Use clear, descriptive titles
- Write 1-2 sentence descriptions
- Include relevant keywords
- Specify content type
- Keep it optimized for LLM consumption

Format:
```
# {path}
Title: {title}
Description: {description}
Keywords: {keywords}
Content-Type: {content_type}
```"""

    GENERATE_WEBSITE_INDEX = """Create a comprehensive documentation index for this website.

Website: {domain}
Total Pages: {page_count}

Pages:
{page_list}

Requirements:
1. Group pages by topic/functionality
2. Create a logical hierarchy
3. Highlight getting started/overview pages
4. Show relationships between pages
5. Suggest reading order for newcomers
6. Mark advanced topics clearly

Format as hierarchical markdown with descriptions."""

    # Quality assessment prompts
    ASSESS_CONTENT_QUALITY = """Assess the quality of this documentation content:

URL: {url}
Content:
{content}

Evaluate:
1. Completeness (0-10): Is all necessary information present?
2. Clarity (0-10): Is it easy to understand?
3. Accuracy (0-10): Does it appear technically correct?
4. Structure (0-10): Is it well-organized?
5. Examples (0-10): Are examples helpful and sufficient?
6. Up-to-date (0-10): Does it seem current?

Provide scores and brief justification for each.
Also suggest top 3 improvements.

Return as JSON."""

    # Comparison prompts
    DETECT_CHANGES = """Compare these two versions of content and identify significant changes:

Previous Version:
{old_content}

New Version:
{new_content}

Identify:
1. Major content additions
2. Major content removals
3. Significant modifications
4. New code examples or features
5. Deprecated elements
6. Breaking changes (if any)

Summarize the changes concisely."""

    # Summarization prompts
    SUMMARIZE_TECHNICAL = """Create a technical summary of this content:

URL: {url}
Content:
{content}

Provide:
1. One-sentence overview
2. Key technical concepts (bullet points)
3. Main takeaways (3-5 points)
4. Technologies/tools used
5. Target audience and prerequisites

Keep it concise but informative."""

    SUMMARIZE_FOR_INDEX = """Create a brief summary for index/catalog purposes:

Title: {title}
URL: {url}
Content Preview:
{content_preview}

Write a 1-2 sentence description that:
- Clearly states what this page covers
- Mentions key technologies/concepts
- Indicates the content type (tutorial, reference, etc.)
- Is compelling for someone browsing an index

Maximum 150 characters."""


class PromptBuilder:
    """Build prompts with context and parameters."""
    
    def __init__(self):
        self.templates = PromptTemplates()
    
    def build_structure_prompt(self, content: str, url: str, title: str,
                             content_type: str = "documentation") -> str:
        """Build content structuring prompt based on type."""
        template_map = {
            "documentation": self.templates.STRUCTURE_DOCUMENTATION,
            "tutorial": self.templates.STRUCTURE_TUTORIAL,
            "api-reference": self.templates.STRUCTURE_API_REFERENCE,
        }
        
        template = template_map.get(content_type, self.templates.STRUCTURE_DOCUMENTATION)
        
        return template.format(
            url=url,
            title=title,
            content=content[:6000]  # Limit content length
        )
    
    def build_extraction_prompt(self, content: str, url: str,
                              extraction_type: str = "key_information") -> str:
        """Build information extraction prompt."""
        if extraction_type == "key_information":
            return self.templates.EXTRACT_KEY_INFORMATION.format(
                url=url,
                content=content[:4000]
            )
        elif extraction_type == "code_patterns":
            return self.templates.EXTRACT_CODE_PATTERNS.format(
                content=content[:4000]
            )
        else:
            return ""
    
    def build_llms_txt_prompt(self, page_data: Dict[str, any]) -> str:
        """Build llms.txt generation prompt."""
        return self.templates.GENERATE_LLMS_TXT.format(
            url=page_data.get("url", ""),
            title=page_data.get("title", ""),
            summary=page_data.get("summary", ""),
            page_type=page_data.get("page_type", "documentation"),
            topics=", ".join(page_data.get("key_topics", [])),
            path=page_data.get("path", "/")
        )
    
    def build_index_prompt(self, domain: str, pages: List[Dict[str, any]]) -> str:
        """Build website index generation prompt."""
        page_list = []
        for page in pages[:30]:  # Limit to 30 pages
            page_list.append(
                f"- {page.get('title', 'Untitled')} ({page.get('url', '')}): "
                f"{page.get('summary', 'No summary')}"
            )
        
        return self.templates.GENERATE_WEBSITE_INDEX.format(
            domain=domain,
            page_count=len(pages),
            page_list="\n".join(page_list)
        )
    
    def build_quality_prompt(self, content: str, url: str) -> str:
        """Build content quality assessment prompt."""
        return self.templates.ASSESS_CONTENT_QUALITY.format(
            url=url,
            content=content[:3000]
        )
    
    def build_change_detection_prompt(self, old_content: str, new_content: str) -> str:
        """Build change detection prompt."""
        return self.templates.DETECT_CHANGES.format(
            old_content=old_content[:2000],
            new_content=new_content[:2000]
        )
    
    def build_summary_prompt(self, content: str, url: str, title: str,
                           summary_type: str = "technical") -> str:
        """Build summarization prompt."""
        if summary_type == "technical":
            return self.templates.SUMMARIZE_TECHNICAL.format(
                url=url,
                content=content[:3000]
            )
        elif summary_type == "index":
            return self.templates.SUMMARIZE_FOR_INDEX.format(
                title=title,
                url=url,
                content_preview=content[:500]
            )
        else:
            return ""


# Singleton instance
prompt_builder = PromptBuilder()


# Convenience functions
def get_structure_prompt(content: str, url: str, title: str,
                        content_type: str = "documentation") -> str:
    """Get content structuring prompt."""
    return prompt_builder.build_structure_prompt(content, url, title, content_type)


def get_llms_txt_prompt(page_data: Dict[str, any]) -> str:
    """Get llms.txt generation prompt."""
    return prompt_builder.build_llms_txt_prompt(page_data)


def get_index_prompt(domain: str, pages: List[Dict[str, any]]) -> str:
    """Get website index generation prompt."""
    return prompt_builder.build_index_prompt(domain, pages)


def get_quality_prompt(content: str, url: str) -> str:
    """Get content quality assessment prompt."""
    return prompt_builder.build_quality_prompt(content, url)