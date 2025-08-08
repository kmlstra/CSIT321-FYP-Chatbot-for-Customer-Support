/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  // Remove the problematic redirects that were causing infinite loops
};

module.exports = nextConfig;