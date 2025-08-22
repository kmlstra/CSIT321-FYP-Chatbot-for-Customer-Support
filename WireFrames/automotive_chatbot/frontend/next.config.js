// Hardcoded configuration for AWS server - No environment detection
// All URLs are hardcoded to AWS IP 13.215.240.173
const AWS_IP = '13.215.240.173';
const FRONTEND_PORT = '3000';
const BACKEND_PORT = '8000';
const RASA_PORT = '5005';

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
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
  // Hardcoded environment variables for AWS server - No dynamic construction
  env: {
    // All URLs hardcoded to AWS IP 13.215.240.173
    NEXT_PUBLIC_DOMAIN: `http://${AWS_IP}`,
    NEXT_PUBLIC_FRONTEND_PORT: FRONTEND_PORT,
    NEXT_PUBLIC_BACKEND_PORT: BACKEND_PORT,
    NEXT_PUBLIC_RASA_PORT: RASA_PORT,
    // Hardcoded URLs - no environment detection
    NEXT_PUBLIC_API_URL: `http://${AWS_IP}:${BACKEND_PORT}`,
    NEXT_PUBLIC_RASA_URL: `http://${AWS_IP}:${RASA_PORT}`,
    NEXT_PUBLIC_WIDGET_URL: `http://${AWS_IP}:${FRONTEND_PORT}`,
    NEXT_PUBLIC_FRONTEND_URL: `http://${AWS_IP}:${FRONTEND_PORT}`,
    NEXT_PUBLIC_BACKEND_URL: `http://${AWS_IP}:${BACKEND_PORT}`,
  },
  // Remove the problematic redirects that were causing infinite loops
};

module.exports = nextConfig;