# Improved Crawler Implementation for Modern Documentation Sites

## Summary

The current crawler pipeline has been updated to better handle modern documentation sites with syntax-highlighted code blocks. The key improvements are:

1. **Code Block Preservation**: Extract code blocks before HTML cleaning to prevent them from being removed
2. **Syntax Highlighting Cleanup**: Remove HTML spans used for syntax highlighting while preserving code content
3. **Markdown Artifacts Removal**: Clean up common artifacts like `[​]` links and standalone "Copy" text
4. **Better Navigation Removal**: More aggressive removal of navigation elements that pollute content

## Implementation Details

### 1. Updated HTML Processor (`src/crawler/processor.py`)

```python
def _extract_code_blocks(self, soup: BeautifulSoup) -> List[tuple]:
    """Extract code blocks and convert them to clean markdown format."""
    code_blocks = []
    
    for pre_tag in soup.find_all('pre'):
        # Extract code content
        code_tag = pre_tag.find('code')
        if code_tag:
            # Modern syntax highlighted code - extract text without spans
            code_text = code_tag.get_text()
        else:
            # Simple pre block
            code_text = pre_tag.get_text()
        
        # Determine language from class attributes
        language = ''
        if pre_tag.get('class'):
            classes = ' '.join(pre_tag.get('class', []))
            # Look for language indicators
            if 'language-' in classes:
                lang_match = re.search(r'language-(\w+)', classes)
                if lang_match:
                    language = lang_match.group(1)
        
        # Create clean code block
        clean_code = f"\n```{language}\n{code_text.strip()}\n```\n"
        
        code_blocks.append((pre_tag, clean_code))
    
    return code_blocks

def html_to_markdown(self, html: str, base_url: str = "") -> str:
    """Convert HTML to Markdown format."""
    try:
        soup = BeautifulSoup(html, 'html5lib')
        
        # Extract and preserve code blocks before cleaning
        code_blocks = self._extract_code_blocks(soup)
        
        # Replace code blocks with placeholders
        for i, (pre_tag, _) in enumerate(code_blocks):
            placeholder = soup.new_tag('p')
            placeholder.string = f"CODE_BLOCK_PLACEHOLDER_{i}"
            pre_tag.replace_with(placeholder)
        
        self._clean_html(soup)
        
        # Convert to markdown
        markdown = md(str(soup), ...)
        
        # Restore code blocks
        for i, (_, clean_code) in enumerate(code_blocks):
            placeholder = f"CODE_BLOCK_PLACEHOLDER_{i}"
            markdown = markdown.replace(placeholder, clean_code)
        
        # Post-process markdown
        markdown = self._post_process_markdown(markdown, base_url)
        
        return markdown
```

### 2. Enhanced Post-Processing

```python
def _post_process_markdown(self, markdown: str, base_url: str) -> str:
    """Post-process markdown content."""
    # ... existing URL fixing ...
    
    # Remove excessive blank lines
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)
    
    # Remove standalone "Copy" lines
    markdown = re.sub(r'^Copy\s*$', '', markdown, flags=re.MULTILINE)
    
    # Remove [​] artifacts
    markdown = re.sub(r'\[​\]', '', markdown)
    
    # Clean up headers with [​] links
    markdown = re.sub(r'^(#{1,6})\s*\[​\]\([^)]+\)\s*(.+)$', r'\1 \2', markdown, flags=re.MULTILINE)
    
    return markdown.strip()
```

### 3. Improved HTML Cleaning

```python
def _clean_html(self, soup: BeautifulSoup) -> None:
    """Clean HTML by removing unwanted elements."""
    # Remove navigation elements by tag
    for tag in ['nav', 'header', 'footer', 'aside']:
        for element in soup.find_all(tag):
            element.decompose()
    
    # Remove elements with navigation-related classes
    nav_classes = ['navigation', 'nav', 'menu', 'sidebar', 'header', 'footer', 
                  'breadcrumb', 'toc', 'table-of-contents']
    for class_name in nav_classes:
        for element in soup.find_all(class_=re.compile(rf'\b{class_name}\b', re.I)):
            element.decompose()
```

## Usage

To use the improved crawler on new sites:

1. The improvements are automatically applied when crawling new websites
2. For existing crawled content, run the update script:

```python
python update_stored_markdown.py
```

## Results

With these improvements:
- Code blocks are properly preserved with syntax highlighting removed
- Navigation and sidebar content is filtered out
- Markdown is cleaner and more readable
- The generated documentation structure matches the original website

## Future Improvements

1. **Language Detection**: Better detection of programming languages from code block classes
2. **Table Preservation**: Enhanced table extraction and formatting
3. **Nested List Handling**: Better preservation of complex nested lists
4. **Image Alt Text**: Improved handling of image descriptions
5. **Custom Element Handlers**: Ability to add site-specific extraction rules