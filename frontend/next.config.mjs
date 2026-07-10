/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone", // produces a minimal, self-contained server bundle for Docker
};

export default nextConfig;