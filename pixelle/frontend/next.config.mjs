// import type { NextConfig } from "next";

// const nextConfig: NextConfig = {
//   /* config options here */
// };

// export default nextConfig;

const nextConfig = {
  async rewrites() {
    return [
      { source: '/pixelle/:path*', destination: 'http://localhost:9004/pixelle/:path*' },
    ];
  },
};
      
export default nextConfig;