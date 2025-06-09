"""AI module for content processing and enhancement."""

from .gemini import (
    GeminiClient,
    get_gemini_client,
    structure_markdown,
    generate_llms_txt_entry,
    extract_code_examples,
    generate_content_index
)
from .prompts import (
    PromptTemplates,
    PromptBuilder,
    prompt_builder,
    get_structure_prompt,
    get_llms_txt_prompt,
    get_index_prompt,
    get_quality_prompt
)
from .tasks import (
    process_page_with_ai,
    generate_website_index_task,
    batch_process_pages_task
)

__all__ = [
    # Gemini client
    "GeminiClient",
    "get_gemini_client",
    "structure_markdown",
    "generate_llms_txt_entry",
    "extract_code_examples",
    "generate_content_index",
    
    # Prompts
    "PromptTemplates",
    "PromptBuilder",
    "prompt_builder",
    "get_structure_prompt",
    "get_llms_txt_prompt",
    "get_index_prompt",
    "get_quality_prompt",
    
    # Tasks
    "process_page_with_ai",
    "generate_website_index_task",
    "batch_process_pages_task"
]