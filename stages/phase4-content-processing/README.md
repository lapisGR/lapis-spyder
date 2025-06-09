# Phase 4: Content Processing

## Overview
Integrate Gemini AI for intelligent content structuring, build advanced markdown processing, and generate llms.txt style documentation indexes.

## Duration: Week 4

## Prerequisites
- Phase 1-3 completed successfully
- Crawling system operational
- Basic markdown conversion working
- Gemini API key obtained

## Checklist

### Day 1-2: Gemini AI Integration
- [ ] Gemini API Setup
  - [ ] Install google-generativeai package
  - [ ] Create Gemini client wrapper
  - [ ] Implement API key management
  - [ ] Add request retry logic
  - [ ] Handle rate limiting
  - [ ] Implement cost tracking
  - [ ] Create response caching
  - [ ] Add timeout handling

- [ ] Prompt Engineering
  - [ ] Create base prompt templates
  - [ ] Design content structuring prompts:
    ```
    System: You are a content structuring expert...
    Task: Convert this raw markdown into well-structured documentation
    Requirements:
    - Clear hierarchy with proper headings
    - Concise, informative sections
    - Preserve all important information
    - Remove redundant content
    - Format code blocks properly
    - Create meaningful link text
    ```
  - [ ] Create prompts for different content types:
    - [ ] Product pages
    - [ ] Documentation
    - [ ] Blog articles
    - [ ] Landing pages
    - [ ] API references
  - [ ] Implement prompt versioning
  - [ ] A/B test prompt effectiveness

### Day 2-3: Advanced Markdown Processing
- [ ] Content Extraction Pipeline
  - [ ] Implement intelligent content extraction:
    - [ ] Main content detection
    - [ ] Navigation removal
    - [ ] Advertisement filtering
    - [ ] Sidebar content handling
    - [ ] Footer removal
  - [ ] Create content quality scoring
  - [ ] Handle different page structures
  - [ ] Preserve semantic HTML meaning

- [ ] Markdown Enhancement
  - [ ] Create markdown post-processing:
    - [ ] Fix heading hierarchy
    - [ ] Normalize link formats
    - [ ] Clean up whitespace
    - [ ] Format tables properly
    - [ ] Handle special characters
  - [ ] Add metadata extraction:
    - [ ] Author information
    - [ ] Publication date
    - [ ] Categories/tags
    - [ ] Related links
  - [ ] Implement markdown validation

### Day 3-4: LLMs.txt Generation
- [ ] Index Structure Design
  - [ ] Create hierarchical page organization
  - [ ] Implement intelligent categorization
  - [ ] Design section grouping logic
  - [ ] Add automatic table of contents
  - [ ] Create cross-references
  - [ ] Handle multi-language content

- [ ] Index Generator
  - [ ] Build llms.txt generator:
    ```python
    class LLMsIndexGenerator:
        def generate_index(website_id):
            # 1. Fetch all processed pages
            # 2. Build hierarchy
            # 3. Create sections
            # 4. Generate descriptions
            # 5. Format as llms.txt
    ```
  - [ ] Implement section templates:
    ```markdown
    # Company Name

    ## Products
    ### Product Category
    - [Product A](url) - Brief description
    - [Product B](url) - Brief description

    ## Documentation
    ### Getting Started
    - [Installation](url) - How to install
    - [Quick Start](url) - Get up and running
    ```
  - [ ] Add automatic summarization
  - [ ] Create link validation
  - [ ] Implement version tracking

### Day 4-5: Processing Pipeline & API
- [ ] Batch Processing System
  - [ ] Create processing queue manager
  - [ ] Implement priority processing
  - [ ] Add batch size optimization
  - [ ] Handle partial failures
  - [ ] Create progress tracking
  - [ ] Implement result aggregation
  - [ ] Add processing metrics

- [ ] Content API Endpoints
  - [ ] GET /content/{website_id}/pages
    - [ ] Pagination support
    - [ ] Filtering options
    - [ ] Search functionality
  - [ ] GET /content/{website_id}/page/{page_id}
    - [ ] Return structured markdown
    - [ ] Include metadata
    - [ ] Show processing history
  - [ ] GET /content/{website_id}/llms.txt
    - [ ] Generate on-demand
    - [ ] Cache results
    - [ ] Support different formats
  - [ ] POST /content/{website_id}/reprocess
    - [ ] Trigger reprocessing
    - [ ] Select specific pages
    - [ ] Use different prompts

### Day 5: Quality Assurance & Testing
- [ ] Content Quality Metrics
  - [ ] Implement quality scoring:
    - [ ] Structure score
    - [ ] Readability score
    - [ ] Completeness score
    - [ ] Link validity score
  - [ ] Create quality dashboards
  - [ ] Add anomaly detection
  - [ ] Implement quality alerts

- [ ] Testing Suite
  - [ ] Unit tests for Gemini integration
  - [ ] Test prompt effectiveness
  - [ ] Validate markdown output
  - [ ] Test llms.txt generation
  - [ ] Performance benchmarks
  - [ ] Cost analysis tests
  - [ ] Integration tests with real sites

## Deliverables
1. Gemini AI integration with prompt management
2. Advanced content extraction and structuring
3. llms.txt index generator
4. Content quality metrics
5. Processing API endpoints
6. Comprehensive test coverage

## Validation Criteria
- [ ] Gemini successfully structures content
- [ ] Markdown output is clean and well-formatted
- [ ] llms.txt matches expected format
- [ ] Processing costs stay within budget
- [ ] Quality scores improve over raw conversion
- [ ] API responses are fast (<2s)
- [ ] Batch processing handles 1000+ pages

## Gemini Prompt Examples

### Content Structuring Prompt
```
You are an expert at structuring web content into clean, organized markdown documentation.

Given the following raw markdown extracted from a webpage, please:
1. Create a clear hierarchy with appropriate heading levels
2. Remove any navigation, ads, or irrelevant content
3. Organize information into logical sections
4. Ensure all important information is preserved
5. Format code blocks with appropriate language tags
6. Make link text descriptive and meaningful
7. Add a brief summary at the beginning if appropriate

Raw Content:
{content}

Please output clean, well-structured markdown.
```

### Index Generation Prompt
```
You are creating a comprehensive documentation index in the style of llms.txt.

Given these page titles and URLs from a website:
{pages}

Please:
1. Organize them into logical categories
2. Create a hierarchical structure
3. Write brief, informative descriptions for each link
4. Group related content together
5. Prioritize important/overview pages at the top
6. Use clear, consistent formatting

Output as a clean markdown index.
```

## Cost Management
- Token usage tracking per request
- Daily/monthly cost limits
- Intelligent caching to reduce API calls
- Batch processing optimization
- Use Gemini Flash for high-volume tasks
- Reserve Gemini Pro for complex structuring

## Performance Targets
- Gemini processing: <5s per page
- Batch processing: 100+ pages/minute
- llms.txt generation: <30s for 1000 pages
- Cache hit rate: >80%
- Quality score improvement: >30%

## Common Issues & Solutions
1. **Gemini rate limits**: Implement exponential backoff
2. **Large content**: Split and process in chunks
3. **Inconsistent output**: Refine prompts, add examples
4. **High costs**: Use caching, batch requests
5. **Timeout errors**: Reduce content size, increase limits

## Testing Commands
```bash
# Test Gemini integration
pytest tests/test_ai.py -v

# Process a single page
curl -X POST http://localhost:8000/content/process-page \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "page_id": "page-uuid",
    "prompt_version": "v1"
  }'

# Generate llms.txt
curl -X GET http://localhost:8000/content/website-id/llms.txt \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check processing metrics
curl -X GET http://localhost:8000/content/metrics \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Next Phase Dependencies
Content processing must be refined and tested before implementing monitoring and scheduling in Phase 5.