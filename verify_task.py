from src.database.mongodb import get_mongo_collection

collection = get_mongo_collection('markdown_documents')

# Check task-creation page
doc = collection.find_one({'url': 'https://docs.hud.so/task-creation'})
if doc:
    content = doc.get('raw_markdown', '')
    print(f'task-creation page:')
    print(f'- Code blocks: {content.count("```") // 2}')
    print(f'- Content length: {len(content)} chars')
    
    # Check for key content
    if '```python' in content:
        print('✓ Python code blocks present')
    if 'gym.make(' in content:
        print('✓ gym.make() examples present')
    if 'Task(' in content:
        print('✓ Task creation examples present')
    if 'Advanced Patterns' in content:
        print('✓ Advanced Patterns section present')
        
    # Save for inspection
    with open('final_task_creation.md', 'w') as f:
        f.write(content)
    print('\nSaved to final_task_creation.md')
else:
    print('task-creation page not found')
