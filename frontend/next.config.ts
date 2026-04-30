import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enforce consistent URLs — no trailing slashes
  // This prevents /analyze and /analyze/ from being treated as two separate pages
  trailingSlash: false,
};

export default nextConfig;
