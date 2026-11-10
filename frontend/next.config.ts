import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    // Product photos come from the scraped store's CDN only.
    remotePatterns: [{ protocol: "https", hostname: "hunnit.com", pathname: "/cdn/**" }],
  },
};

export default nextConfig;
