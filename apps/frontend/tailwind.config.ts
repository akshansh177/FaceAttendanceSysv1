import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["system-ui", "-apple-system", "Segoe UI", "Roboto", "Helvetica Neue", "Arial", "sans-serif"],
      },
      colors: {
        brand: {
          50: "#e8f4fc",
          100: "#cfe8fb",
          200: "#9ec5e8",
          500: "#3d9aff",
          600: "#007bff",
          700: "#0066d6",
          800: "#0052ad",
        },
        theme: {
          bg: "var(--background)",
          panel: "var(--surface)",
          ink: "var(--foreground)",
          muted: "var(--foreground-muted)",
          sidebar: "var(--sidebar)",
        },
      },
      boxShadow: {
        card: "var(--shadow-card)",
        panel: "var(--shadow-panel)",
      },
      borderRadius: {
        "2xl": "var(--radius-2xl)",
      },
    },
  },
  plugins: [],
};
export default config;
