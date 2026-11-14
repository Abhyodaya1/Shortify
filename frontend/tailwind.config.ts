import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        dominant: "var(--color-dominant)",
        canvas: "var(--color-canvas)",
        surface: "var(--color-surface)",
        surfaceCard: "var(--color-surface-card)",
        surfaceAlt: "var(--color-surface-alt)",
        "surface-container": "var(--color-surface-container)",
        "surface-container-low": "var(--color-surface-container-low)",
        "surface-container-lowest": "var(--color-surface-container-lowest)",
        "surface-container-high": "var(--color-surface-container-high)",
        "surface-container-highest": "var(--color-surface-container-highest)",
        primary: "var(--color-primary)",
        "on-primary": "var(--color-white)",
        emphasis: "var(--color-emphasis)",
        secondary: "var(--color-secondary)",
        "secondary-container": "var(--color-accent-lime)",
        "on-secondary-container": "var(--color-primary)",
        "tertiary-fixed": "var(--color-accent-mint)",
        "tertiary-fixed-dim": "var(--color-accent-mint-dim)",
        secondaryTint: "var(--color-secondary-tint)",
        muted: "var(--color-muted)",
        subtle: "var(--color-subtle)",
        outline: "var(--color-outline)",
        "outline-variant": "var(--color-outline-variant)",
        borderToken: "var(--color-border)",
        borderSubtle: "var(--color-border-subtle)",
        accent: "var(--color-accent)",
        accentLime: "var(--color-accent-lime)",
        accentMint: "var(--color-accent-mint)",
        accentHover: "var(--color-accent-hover)",
        accentActive: "var(--color-accent-active)",
        accentTint: "var(--color-accent-tint)",
        accentDark: "var(--color-accent-dark)",
        destructiveToken: "var(--color-destructive)",
      },
      spacing: {
        1: "var(--space-1)",   // 8px
        2: "var(--space-2)",   // 16px
        3: "var(--space-3)",   // 24px
        4: "var(--space-4)",   // 32px
        6: "var(--space-6)",   // 48px
        8: "var(--space-8)",   // 64px
        12: "var(--space-12)", // 96px
      },
      borderRadius: {
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
        xl: "var(--radius-xl)",
        full: "var(--radius-full)",
      },
      boxShadow: {
        sm: "var(--shadow-sm)",
        md: "var(--shadow-md)",
        lg: "var(--shadow-lg)",
        hard: "var(--shadow-hard)",
        "hard-sm": "var(--shadow-hard-sm)",
        "hard-lg": "var(--shadow-hard-lg)",
        "hard-lime": "var(--shadow-hard-lime)",
        "hard-mint": "var(--shadow-hard-mint)",
      },
      fontFamily: {
        sans: ["var(--font-sans)"],
        display: ["var(--font-display)"],
        headline: ["var(--font-display)"],
        body: ["var(--font-body)"],
        mono: ["var(--font-mono)"],
        serif: ["var(--font-sans)"],
        manrope: ["var(--font-body)"],
        inter: ["var(--font-body)"],
        outfit: ["var(--font-display)"],
      },
      transitionDuration: {
        fast: "var(--duration-fast)",
        normal: "var(--duration-normal)",
        slow: "var(--duration-slow)",
      },
      transitionTimingFunction: {
        out: "var(--ease-out)",
        inOut: "var(--ease-in-out)",
      },
    },
  },
  plugins: [],
};

export default config;
