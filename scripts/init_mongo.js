// Initialize MongoDB database for Lapis Spider

// Switch to the database
db = db.getSiblingDB('lapis_spider');

// Create collections with validation
db.createCollection('raw_html', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['crawl_job_id', 'page_id', 'url', 'raw_html', 'crawled_at'],
      properties: {
        crawl_job_id: {
          bsonType: 'string',
          description: 'UUID of the crawl job'
        },
        page_id: {
          bsonType: 'string',
          description: 'UUID of the page from PostgreSQL'
        },
        url: {
          bsonType: 'string',
          description: 'Full URL of the page'
        },
        raw_html: {
          bsonType: 'string',
          description: 'Raw HTML content'
        },
        headers: {
          bsonType: 'object',
          description: 'HTTP response headers'
        },
        status_code: {
          bsonType: 'int',
          description: 'HTTP status code'
        },
        crawled_at: {
          bsonType: 'date',
          description: 'Timestamp when crawled'
        },
        content_type: {
          bsonType: 'string',
          description: 'Content-Type header value'
        },
        size_bytes: {
          bsonType: 'int',
          description: 'Size of the raw HTML in bytes'
        }
      }
    }
  }
});

db.createCollection('markdown_documents', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['page_id', 'website_id', 'url', 'raw_markdown', 'processed_at'],
      properties: {
        page_id: {
          bsonType: 'string',
          description: 'UUID of the page'
        },
        website_id: {
          bsonType: 'string',
          description: 'UUID of the website'
        },
        url: {
          bsonType: 'string',
          description: 'Full URL of the page'
        },
        raw_markdown: {
          bsonType: 'string',
          description: 'Initial markdown conversion'
        },
        structured_markdown: {
          bsonType: 'string',
          description: 'Gemini-processed markdown'
        },
        metadata: {
          bsonType: 'object',
          properties: {
            title: { bsonType: 'string' },
            description: { bsonType: 'string' },
            headings: { bsonType: 'array' },
            links: { bsonType: 'array' },
            images: { bsonType: 'array' }
          }
        },
        gemini_prompt_used: {
          bsonType: 'string',
          description: 'Prompt used for Gemini processing'
        },
        processed_at: {
          bsonType: 'date',
          description: 'Timestamp when processed'
        },
        version: {
          bsonType: 'int',
          description: 'Document version number'
        }
      }
    }
  }
});

db.createCollection('website_indexes', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['website_id', 'index_content', 'generated_at'],
      properties: {
        website_id: {
          bsonType: 'string',
          description: 'UUID of the website'
        },
        index_content: {
          bsonType: 'string',
          description: 'The full llms.txt content'
        },
        page_tree: {
          bsonType: 'object',
          description: 'Hierarchical structure of pages'
        },
        generated_at: {
          bsonType: 'date',
          description: 'Timestamp when generated'
        },
        version: {
          bsonType: 'int',
          description: 'Index version number'
        }
      }
    }
  }
});

// Create indexes
db.raw_html.createIndex({ crawl_job_id: 1 });
db.raw_html.createIndex({ page_id: 1 });
db.raw_html.createIndex({ url: 1 });
db.raw_html.createIndex({ crawled_at: -1 });

db.markdown_documents.createIndex({ page_id: 1 });
db.markdown_documents.createIndex({ website_id: 1 });
db.markdown_documents.createIndex({ url: 1 });
db.markdown_documents.createIndex({ processed_at: -1 });
db.markdown_documents.createIndex({ version: -1 });

db.website_indexes.createIndex({ website_id: 1 });
db.website_indexes.createIndex({ generated_at: -1 });
db.website_indexes.createIndex({ version: -1 });

// Create text indexes for search
db.markdown_documents.createIndex({ 
  'raw_markdown': 'text', 
  'structured_markdown': 'text',
  'metadata.title': 'text',
  'metadata.description': 'text'
});

db.website_indexes.createIndex({ 'index_content': 'text' });

// Create capped collection for logs (optional)
db.createCollection('crawl_logs', {
  capped: true,
  size: 100 * 1024 * 1024, // 100MB
  max: 100000 // Max 100k documents
});

print('MongoDB initialization completed successfully');