import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AppLayout } from "@/components/layout/app-layout";
import { LoadingProvider } from "@/contexts/LoadingContext";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { Toaster } from "@/components/ui/sonner";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "Cybersecurity Intelligence Platform",
  description: "Comprehensive cybersecurity intelligence platform for threat analysis",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <LoadingProvider>
          <AppLayout>{children}</AppLayout>
          <LoadingSpinner />
          <Toaster />
        </LoadingProvider>
      </body>
    </html>
  );
}