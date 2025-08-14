const path = require('path');
const fs = require('fs');

// Load environment variables from backend/.env (only if file exists)
const envPath = path.join(__dirname, '../backend/.env');
if (fs.existsSync(envPath)) {
  require('dotenv').config({ path: envPath });
}

// Default values for Docker build
const defaultDomain = process.env.NEXT_PUBLIC_DOMAIN || 'http://localhost';
const defaultFrontendPort = process.env.NEXT_PUBLIC_FRONTEND_PORT || '3000';
const defaultBackendPort = process.env.NEXT_PUBLIC_BACKEND_PORT || '8000';
const defaultRasaPort = process.env.NEXT_PUBLIC_RASA_PORT || '5005';

/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    // Disable ESLint during builds
    ignoreDuringBuilds: true,
  },
  // experimental: {
  //   appDir: true, // Deprecated in Next.js 15
  // },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
      {
        protocol: 'http',
        hostname: '**',
      },
    ],
  },
  // Environment variables with defaults for Docker build
  env: {
    // Unified domain configuration - construct URLs dynamically
    NEXT_PUBLIC_DOMAIN: defaultDomain,
    NEXT_PUBLIC_FRONTEND_PORT: defaultFrontendPort,
    NEXT_PUBLIC_BACKEND_PORT: defaultBackendPort,
    NEXT_PUBLIC_RASA_PORT: defaultRasaPort,
    // Constructed URLs using domain:port format
    NEXT_PUBLIC_API_URL: `${defaultDomain}:${defaultBackendPort}`,
    NEXT_PUBLIC_RASA_URL: `${defaultDomain}:${defaultRasaPort}`,
    NEXT_PUBLIC_WIDGET_URL: `${defaultDomain}:${defaultFrontendPort}`,
    NEXT_PUBLIC_FRONTEND_URL: `${defaultDomain}:${defaultFrontendPort}`,
    NEXT_PUBLIC_BACKEND_URL: `${defaultDomain}:${defaultBackendPort}`,
  },
  // Remove the problematic redirects that were causing infinite loops
};

module.exports = nextConfig;