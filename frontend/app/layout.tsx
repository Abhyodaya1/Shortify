import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("http://localhost:3000"),
  title: "Motion — The General Video Agent",
  description: "Create and edit videos from a brief, your footage, or a reference. Autonomous AI video agent.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[var(--color-dominant)] text-[var(--color-secondary)] antialiased">
        {children}
      </body>
    </html>
  );
}
