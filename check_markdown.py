from src.database.mongodb import get_mongo_collection

# Get markdown collection
markdown_collection = get_mongo_collection('markdown_documents')

# Find task-creation page
doc = markdown_collection.find_one({'url': 'https://docs.hud.so/task-creation'})

if doc and doc.get('raw_markdown'):
    markdown = doc['raw_markdown']
    
    # Count code blocks
    code_count = markdown.count('```')
    print(f'Total code blocks in document: {code_count // 2}')
    
    # Check if Advanced Patterns has content
    if 'Advanced Patterns' in markdown:
        print('\nAdvanced Patterns section found')
        # Find position
        pos = markdown.find('Advanced Patterns')
        # Show some context
        print('\nContext around Advanced Patterns:')
        print(markdown[pos-50:pos+300])
    
    # Save to file for inspection
    with open('task_creation_markdown.md', 'w') as f:
        f.write(markdown)
    print('\nFull markdown saved to task_creation_markdown.md')