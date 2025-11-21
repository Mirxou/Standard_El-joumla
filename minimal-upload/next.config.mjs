/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    // Allow opening the dev server from LAN IPs without CORS warnings
    allowedDevOrigins: [
      "http://localhost:3000",
      "http://127.0.0.1:3000",
      // Add your LAN IP here if it changes
      "http://192.168.131.49:3000",
    ],
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
}

export default nextConfig
