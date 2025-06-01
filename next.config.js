/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  
  // Image optimization configuration
  images: {
    domains: ['localhost', 'your-production-domain.com'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    formats: ['image/webp'],
    minimumCacheTTL: 60,
    dangerouslyAllowSVG: false,
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
  },
  
  // Internationalization configuration
  i18n: {
    locales: ['en', 'es', 'fr', 'de'],
    defaultLocale: 'en',
    localeDetection: true,
  },
  
  // Configure rewrites to proxy API requests to the FastAPI backend in development
  // This routes requests through Kong API Gateway (port 8080) which then forwards to FastAPI (port 8000)
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.BACKEND_URL || 'http://localhost:8080/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;