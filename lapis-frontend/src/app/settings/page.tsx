'use client';

import { useState, useEffect } from 'react';

export default function SettingsPage() {
  const [apiUrl, setApiUrl] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    // Load current API URL
    const currentUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    setApiUrl(currentUrl);
  }, []);

  const handleSave = () => {
    // In a real app, you'd save this to localStorage or a config file
    localStorage.setItem('api_url', apiUrl);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
    
    // Note: Changing env variables requires app restart
    alert('Settings saved! Note: Changing the API URL requires restarting the application.');
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Settings</h1>

      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">API Configuration</h2>
        
        <div className="space-y-4">
          <div>
            <label htmlFor="apiUrl" className="block text-sm font-medium text-gray-700 mb-1">
              API URL
            </label>
            <input
              id="apiUrl"
              type="url"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="http://localhost:8000"
            />
            <p className="mt-1 text-sm text-gray-600">
              The URL where your Lapis Spider API is running
            </p>
          </div>

          <div className="pt-4">
            <button
              onClick={handleSave}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Save Settings
            </button>
            
            {saved && (
              <span className="ml-3 text-green-600">Settings saved!</span>
            )}
          </div>
        </div>
      </div>

      <div className="mt-8 bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Environment Variables</h2>
        
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-sm text-gray-700 mb-3">
            Current environment variables:
          </p>
          <div className="space-y-2 font-mono text-sm">
            <div className="flex">
              <span className="text-gray-600 w-48">NEXT_PUBLIC_API_URL:</span>
              <span className="text-gray-900">{process.env.NEXT_PUBLIC_API_URL || 'Not set'}</span>
            </div>
            <div className="flex">
              <span className="text-gray-600 w-48">NEXT_PUBLIC_APP_NAME:</span>
              <span className="text-gray-900">{process.env.NEXT_PUBLIC_APP_NAME || 'Not set'}</span>
            </div>
          </div>
        </div>

        <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            <strong>Note:</strong> To permanently change environment variables, update the <code className="bg-yellow-100 px-1 py-0.5 rounded">.env.local</code> file and restart the application.
          </p>
        </div>
      </div>

      <div className="mt-8 bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">API Information</h2>
        
        <div className="space-y-3 text-sm">
          <div>
            <h3 className="font-medium text-gray-900">Authentication</h3>
            <p className="text-gray-600">The API uses JWT tokens for authentication. Tokens are stored in localStorage.</p>
          </div>
          
          <div>
            <h3 className="font-medium text-gray-900">Required Services</h3>
            <ul className="list-disc list-inside text-gray-600 mt-1">
              <li>PostgreSQL (main database)</li>
              <li>MongoDB (content storage)</li>
              <li>Redis (cache and queue)</li>
              <li>Google Gemini API (AI processing)</li>
            </ul>
          </div>
          
          <div>
            <h3 className="font-medium text-gray-900">API Documentation</h3>
            <p className="text-gray-600">
              When running in development mode, API documentation is available at{' '}
              <a 
                href={`${apiUrl}/docs`} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-700"
              >
                {apiUrl}/docs
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}