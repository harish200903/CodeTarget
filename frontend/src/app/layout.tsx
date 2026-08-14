import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CodeTarget | Company-Specific Coding-Round Preparation",
  description: "Target company coding-round preparation platform with personalized recommendations, progressive hints, and readiness analytics.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased bg-[#0B0F17] text-slate-100 selection:bg-indigo-500/30 selection:text-indigo-200">
        {children}
      </body>
    </html>
  );
}
