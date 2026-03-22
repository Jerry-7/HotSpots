import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: "#0f172a",
        panel: "#111827",
        accent: "#14b8a6",
        warm: "#f59e0b"
      }
    }
  },
  plugins: [],
};

export default config;
