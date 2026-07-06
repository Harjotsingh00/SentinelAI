import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        sentinel: {
          bg: "#0B0F19",
          panel: "#111827",
          border: "#1F2937",
          accent: "#3B82F6",
          danger: "#EF4444",
          warning: "#F59E0B",
          success: "#10B981",
        },
      },
      boxShadow: {
        panel: "0 1px 2px 0 rgba(0,0,0,0.3)",
      },
    },
  },
  plugins: [],
};

export default config;
