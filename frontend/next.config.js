/** @type {import('next').NextConfig} */
const path = require('path');

const nextConfig = {
  reactStrictMode: false,
  basePath: process.env.NEXT_PUBLIC_BASE_PATH,
  assetPrefix: process.env.NEXT_PUBLIC_BASE_PATH,
  outputFileTracingRoot: path.join(__dirname),
  images: {
    domains: [
      'images.unsplash.com',
      'i.ibb.co',
      'scontent.fotp8-1.fna.fbcdn.net',
    ],
    unoptimized: true,
  },
  // Performance optimizations
  experimental: {
    optimizePackageImports: [
      '@chakra-ui/react',
      'react-icons',
      'apexcharts',
      'react-apexcharts',
      'axios',
    ],
  },
  // Compiler options
  compiler: {
    // Temporarily allow console.log for debugging
    // removeConsole: process.env.NODE_ENV === 'production',
  },
  // Module ID generation for better caching
  modularizeImports: {
    'react-icons/fa': {
      transform: 'react-icons/fa/{{member}}',
    },
    'react-icons/fi': {
      transform: 'react-icons/fi/{{member}}',
    },
    'react-icons/ai': {
      transform: 'react-icons/ai/{{member}}',
    },
    'react-icons/md': {
      transform: 'react-icons/md/{{member}}',
    },
  },
  // Webpack configuration to fix module resolution
  webpack: (config, { isServer }) => {
    // Add the frontend node_modules to the resolution paths
    config.resolve.modules = [
      path.join(__dirname, 'node_modules'),
      'node_modules',
      ...(config.resolve.modules || [])
    ];
    return config;
  },
  // Rewrites handled by Kubernetes ingress in production
  // For local development, use NEXT_PUBLIC_BACKEND_URL or rely on K8s routing
};

module.exports = nextConfig;
