// API Configuration
// Update API_BASE_URL to your machine's IP address when hosting for external access
// Or use environment variable VITE_API_BASE_URL for dynamic configuration

// For local development only
// const API_BASE_URL = 'http://localhost:8000';

// For network access - replace with your machine's IP address
// Example: const API_BASE_URL = 'http://192.168.1.100:8000';

// Check for environment variable first, then fall back to automatic detection
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
  (window.location.hostname === 'localhost' 
    ? 'http://localhost:8000'
    : `http://${window.location.hostname}:8000`);

// Helper function to build API URLs
export const apiUrl = (path: string): string => {
  const baseUrl = API_BASE_URL.replace(/\/$/, ''); // Remove trailing slash
  const pathWithSlash = path.startsWith('/') ? path : `/${path}`;
  return `${baseUrl}${pathWithSlash}`;
};

// Helper function to handle ngrok requests with proper headers
export const fetchWithNgrokHeaders = (url: string, options: RequestInit = {}) => {
  // Add ngrok bypass header if using ngrok URL
  if (API_BASE_URL.includes('ngrok')) {
    options.headers = {
      ...options.headers,
      'ngrok-skip-browser-warning': 'true',
    };
  }
  return fetch(url, options);
};

export { API_BASE_URL };