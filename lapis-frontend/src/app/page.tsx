'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';

export default function HomePage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [healthStatus, setHealthStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    setIsAuthenticated(!!token);
    setLoading(false);

    // Check API health - commented out for now if backend is not running
    // api.checkHealth().then(setHealthStatus).catch(console.error);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="spinner w-8 h-8"></div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-600 to-blue-800 p-8 mb-8 text-white">
        <div className="relative z-10 max-w-3xl">
          <h1 className="text-5xl font-bold mb-4">
            Welcome to Lapis Spider
          </h1>
          <p className="text-xl mb-8 text-blue-100">
            AI-powered web crawling system that generates structured documentation in llms.txt format.
          </p>

          {!isAuthenticated ? (
            <div className="flex flex-wrap gap-4">
              <Link
                href="/login"
                className="inline-flex items-center px-6 py-3 bg-white text-blue-600 font-medium rounded-lg hover:bg-blue-50 transition-all transform hover:scale-105"
              >
                Login
              </Link>
              <Link
                href="/register"
                className="inline-flex items-center px-6 py-3 bg-blue-700 text-white font-medium rounded-lg hover:bg-blue-600 transition-all transform hover:scale-105"
              >
                Create Account
              </Link>
            </div>
          ) : (
            <div className="flex flex-wrap gap-4">
              <Link
                href="/websites"
                className="inline-flex items-center px-6 py-3 bg-white text-blue-600 font-medium rounded-lg hover:bg-blue-50 transition-all transform hover:scale-105"
              >
                My Websites
                <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
              <Link
                href="/websites/new"
                className="inline-flex items-center px-6 py-3 bg-blue-700 text-white font-medium rounded-lg hover:bg-blue-600 transition-all transform hover:scale-105"
              >
                Add Website
                <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </Link>
            </div>
          )}
        </div>
        
        {/* Background decoration */}
        <div className="absolute top-0 right-0 -mt-16 -mr-16 w-64 h-64 bg-blue-500 rounded-full opacity-20"></div>
        <div className="absolute bottom-0 left-0 -mb-16 -ml-16 w-64 h-64 bg-blue-400 rounded-full opacity-20"></div>
      </div>

      <div className="grid gap-8 md:grid-cols-2">
        {/* System Status */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-semibold">System Status</h2>
            <div className={`w-3 h-3 rounded-full ${healthStatus?.status === 'healthy' ? 'bg-green-500' : 'bg-gray-400'} animate-pulse`}></div>
          </div>
          
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-100 rounded-lg">
              <span className="font-medium">API Status</span>
              <span className="px-3 py-1 rounded-full text-xs font-medium bg-gray-200 text-gray-600">
                {healthStatus ? healthStatus.status : 'Not Connected'}
              </span>
            </div>
            
            <div className="text-sm text-gray-500 text-center mt-4">
              Backend API not connected. Please ensure the backend is running on port 8000.
            </div>
          </div>
        </div>

        {/* Features */}
        <div className="card p-6">
          <h2 className="text-2xl font-semibold mb-4">Features</h2>
          <div className="space-y-4">
            {[
              {
                title: 'High-Performance Crawling',
                description: 'Powered by Spider-rs Rust crawler',
                icon: '⚡'
              },
              {
                title: 'AI Content Processing',
                description: 'Google Gemini for intelligent structuring',
                icon: '🤖'
              },
              {
                title: 'LLMs.txt Generation',
                description: 'Structured documentation format',
                icon: '📄'
              },
              {
                title: 'Change Detection',
                description: 'Monitor websites for updates',
                icon: '🔍'
              }
            ].map((feature, index) => (
              <div key={index} className="flex items-start gap-3">
                <span className="text-2xl">{feature.icon}</span>
                <div>
                  <h3 className="font-semibold">{feature.title}</h3>
                  <p className="text-sm text-gray-600">{feature.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* How it Works */}
      <div className="mt-12 card p-8">
        <h2 className="text-3xl font-semibold mb-8 text-center">How It Works</h2>
        <div className="grid gap-8 md:grid-cols-4">
          {[
            { step: '1', title: 'Add Website', description: 'Enter the URL you want to crawl' },
            { step: '2', title: 'Configure Crawl', description: 'Set depth, page limits, and rules' },
            { step: '3', title: 'AI Processing', description: 'Content is analyzed and structured' },
            { step: '4', title: 'View Results', description: 'Access your llms.txt documentation' }
          ].map((item, index) => (
            <div key={index} className="text-center">
              <div className="w-12 h-12 bg-blue-500 text-white rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-4">
                {item.step}
              </div>
              <h3 className="font-semibold mb-2">{item.title}</h3>
              <p className="text-sm text-gray-600">{item.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}