/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Turbopack configuration (Next.js 16+)
  turbopack: {},
  
  // Image optimization
  images: {
    formats: ['image/avif', 'image/webp'],
  },
  
  // Code splitting
  // experimental: {
  //   optimizeCss: true, // Requires critters package
  // },
  
  // Bundle analyzer (optional)
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Optimize bundle size
      config.optimization = {
        ...config.optimization,
        splitChunks: {
          chunks: 'all',
          cacheGroups: {
            default: false,
            vendors: false,
            // Vendor chunk
            vendor: {
              name: 'vendor',
              chunks: 'all',
              test: /node_modules/,
              priority: 20,
            },
            // Common chunk
            common: {
              name: 'common',
              minChunks: 2,
              chunks: 'all',
              priority: 10,
              reuseExistingChunk: true,
              enforce: true,
            },
          },
        },
      }
    }
    return config
  },
  
  // Compression
  compress: true,
  
  // Headers for caching
  async headers() {
    return [
      {
        source: '/:all*(svg|jpg|png|webp|avif)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        source: '/_next/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
    ]
  },
}

module.exports = nextConfig

