import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  env: {
    // 这里读取系统环境变量，如果不存在则使用默认值
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000' ,
    BACKEND_PORT: process.env.BACKEND_PORT || '8000',
  }
};

export default nextConfig;
