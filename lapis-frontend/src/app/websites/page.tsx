'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Website, CrawlJob } from '@/types';

export default function WebsitesPage() {
  const router = useRouter();
  const [websites, setWebsites] = useState<Website[]>([]);
  const [crawlJobs, setCrawlJobs] = useState<Record<string, CrawlJob>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadWebsites();
  }, []);

  const loadWebsites = async () => {
    try {
      const result = await api.getWebsites();
      const data = result.data || [];
      setWebsites(data);
      
      // Load latest crawl job for each website
      const jobs: Record<string, CrawlJob> = {};
      for (const website of data) {
        try {
          const historyResult = await api.getCrawlHistory(website.id);
          const history = historyResult.data || [];
          if (history.length > 0) {
            jobs[website.id] = history[0];
          }
        } catch (err) {
          console.error(`Failed to load crawl history for ${website.id}:`, err);
        }
      }
      setCrawlJobs(jobs);
    } catch (err: any) {
      setError(err.message || 'Failed to load websites');
      if (err.message.includes('401')) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleStartCrawl = async (websiteId: string) => {
    try {
      const result = await api.startCrawl(websiteId);
      alert(`Crawl started! Job ID: ${result.crawl_job_id}`);
      // Reload to show new job
      loadWebsites();
    } catch (err: any) {
      alert(`Failed to start crawl: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg text-gray-600">Loading websites...</div>
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
    <div className="max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">My Websites</h1>
        <Link
          href="/websites/new"
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Add Website
        </Link>
      </div>

      {websites.length === 0 ? (
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <p className="text-gray-600 mb-4">You haven't added any websites yet.</p>
          <Link
            href="/websites/new"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Add Your First Website
          </Link>
        </div>
      ) : (
        <div className="grid gap-6">
          {websites.map((website) => {
            const lastJob = crawlJobs[website.id];
            
            return (
              <div key={website.id} className="bg-white rounded-lg shadow-md p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900 mb-1">
                      {website.name}
                    </h2>
                    <a
                      href={website.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-700 flex items-center gap-1"
                    >
                      {website.url}
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  </div>
                  
                  <div className="flex gap-2">
                    <Link
                      href={`/websites/${website.id}/llms`}
                      className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-sm"
                    >
                      View LLMs.txt
                    </Link>
                    <button
                      onClick={() => handleStartCrawl(website.id)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
                    >
                      Start Crawl
                    </button>
                  </div>
                </div>

                {lastJob && (
                  <div className="border-t pt-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Last Crawl:</span>
                        <p className="font-medium">
                          {new Date(lastJob.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <div>
                        <span className="text-gray-600">Status:</span>
                        <p className={`font-medium ${
                          lastJob.status === 'completed' ? 'text-green-600' :
                          lastJob.status === 'failed' ? 'text-red-600' :
                          lastJob.status === 'running' ? 'text-blue-600' :
                          'text-gray-600'
                        }`}>
                          {lastJob.status}
                        </p>
                      </div>
                      <div>
                        <span className="text-gray-600">Pages Crawled:</span>
                        <p className="font-medium">{lastJob.pages_crawled || 0}</p>
                      </div>
                      <div>
                        <span className="text-gray-600">Duration:</span>
                        <p className="font-medium">
                          {lastJob.statistics?.duration_seconds 
                            ? `${Math.round(lastJob.statistics.duration_seconds)}s`
                            : '-'}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}