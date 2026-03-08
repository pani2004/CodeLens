import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Toaster } from "sonner";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "CodeLens AI - Understand Any Codebase in Minutes",
  description: "AI-powered codebase analysis and exploration. Upload any GitHub repository and get instant insights, dependency graphs, and intelligent Q&A.",
  keywords: ["code analysis", "AI", "GitHub", "codebase explorer", "developer tools"],
  authors: [{ name: "CodeLens AI" }],
  openGraph: {
    title: "CodeLens AI - Understand Any Codebase in Minutes",
    description: "AI-powered codebase analysis and exploration",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.variable} font-sans antialiased`}
      >
        {children}
        <Toaster position="bottom-right" richColors closeButton />
      </body>
    </html>
  );
}
