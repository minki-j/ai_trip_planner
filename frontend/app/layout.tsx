import './globals.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { Toaster } from '@/components/ui/toaster';
import { ThemeProvider } from '@/components/theme-provider';
import { Navigation } from '@/components/navigation';
import { AuthProvider } from '@/components/auth-provider';
import { Suspense } from 'react';
import { ThemeColor } from '@/components/theme-color';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: "EnglishTutor",
  description:
    "Improve your English writing skills with AI-powered corrections and quizzes",
  icons: {
    icon: [
      { url: "/favicon/favicon-16x16.png", sizes: "16x16", type: "image/png" },
      { url: "/favicon/favicon-32x32.png", sizes: "32x32", type: "image/png" },
      { url: "/favicon/favicon.ico", sizes: "48x48", type: "image/x-icon" },
    ],
    apple: [
      {
        url: "/favicon/apple-touch-icon.png",
        sizes: "180x180",
        type: "image/png",
      },
    ],
    other: [
      {
        rel: "android-chrome-192x192",
        url: "/favicon/android-chrome-192x192.png",
      },
      {
        rel: "android-chrome-512x512",
        url: "/favicon/android-chrome-512x512.png",
      },
    ],
  },
  manifest: "/favicon/site.webmanifest",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>  
        <meta name="theme-color" content="hsl(0, 0%, 3.9%)" />
      </head>
      <body className={inter.className}>
        <AuthProvider>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            <ThemeColor />
            <Suspense
              fallback={
                <div className="min-h-screen bg-background animate-pulse">
                  <div className="h-16 bg-muted" />
                  <main className="container mx-auto px-4 py-8 space-y-4">
                    <div className="h-8 w-[200px] bg-muted rounded" />
                    <div className="h-32 bg-muted rounded" />
                    <div className="grid gap-4">
                      <div className="h-20 bg-muted rounded" />
                      <div className="h-20 bg-muted rounded" />
                    </div>
                  </main>
                </div>
              }
            >
              <div className="min-h-screen bg-background">
                <Navigation />
                <main className="container mx-auto px-4 py-8">{children}</main>
              </div>
            </Suspense>
            <Toaster />
          </ThemeProvider>
        </AuthProvider>
      </body>
    </html>
  );
}