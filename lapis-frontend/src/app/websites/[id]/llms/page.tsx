'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Page } from '@/types';

export default function LlmsTxtPage() {
  const params = useParams();
  const router = useRouter();
  const websiteId = params.id as string;
  
  const [llmsTxt, setLlmsTxt] = useState<string>('');
  const [pages, setPages] = useState<Page[]>([]);
  const [selectedPageId, setSelectedPageId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadContent();
  }, [websiteId]);

  const loadContent = async () => {
    try {
      // Load llms.txt for the main site
      const [llmsContent, pagesData] = await Promise.all([
        api.getLlmsTxt(websiteId),
        api.getPages(websiteId)
      ]);
      
      setLlmsTxt(llmsContent);
      setPages(pagesData);
    } catch (err: any) {
      setError(err.message || 'Failed to load content');
      if (err.message.includes('401')) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePageSelect = async (pageId: string) => {
    setSelectedPageId(pageId);
    try {
      // For now, show the same llms.txt content
      // In a full implementation, you'd generate page-specific content
      const pageContent = await api.getPageContent(websiteId, pageId);
      // You could format this as a page-specific llms.txt section
    } catch (err) {
      console.error('Failed to load page content:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg text-gray-600">Loading content...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">LLMs.txt Content</h1>
        <Link
          href="/websites"
          className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
        >
          Back to Websites
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Pages Sidebar */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-md p-4">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Pages</h2>
            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              <button
                onClick={() => setSelectedPageId(null)}
                className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
                  selectedPageId === null
                    ? 'bg-blue-100 text-blue-700'
                    : 'hover:bg-gray-100'
                }`}
              >
                <div className="font-medium">Main Site</div>
                <div className="text-xs text-gray-600">Complete llms.txt</div>
              </button>
              
              {pages.map((page) => (
                <button
                  key={page.id}
                  onClick={() => handlePageSelect(page.id)}
                  className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
                    selectedPageId === page.id
                      ? 'bg-blue-100 text-blue-700'
                      : 'hover:bg-gray-100'
                  }`}
                >
                  <div className="font-medium truncate">{page.title || 'Untitled'}</div>
                  <div className="text-xs text-gray-600 truncate">{page.url}</div>
                  {page.ai_processed && (
                    <span className="inline-block mt-1 px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded">
                      AI Processed
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Content Display */}
        <div className="lg:col-span-3">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-900">
                {selectedPageId ? 'Page Content' : 'Complete LLMs.txt'}
              </h2>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(llmsTxt);
                  alert('Copied to clipboard!');
                }}
                className="px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md text-sm transition-colors"
              >
                Copy to Clipboard
              </button>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-4 overflow-x-auto">
              <pre className="text-sm text-gray-800 whitespace-pre-wrap font-mono">
                {llmsTxt || 'No llms.txt content generated yet. Make sure the pages have been processed with AI.'}
              </pre>
            </div>

            {!llmsTxt && (
              <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">
                  <strong>Note:</strong> To generate llms.txt content, ensure that:
                </p>
                <ul className="list-disc list-inside mt-2 text-sm text-yellow-700">
                  <li>The website has been crawled</li>
                  <li>Pages have been processed with AI</li>
                  <li>The AI processing has completed successfully</li>
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}