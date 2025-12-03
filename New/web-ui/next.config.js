/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'standalone',
    reactStrictMode: true,

    // Next.js 16: Enable Cache Components (PPR replacement)
    cacheComponents: true,

    // Note: Turbopack is now stable and enabled via --turbopack flag in dev
    // Note: React Compiler requires babel-plugin-react-compiler - can be added later

    env: {
        NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001',
    },

    async rewrites() {
        return [
            {
                source: '/api/:path*',
                destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/:path*`,
            },
        ];
    },
};

module.exports = nextConfig;
