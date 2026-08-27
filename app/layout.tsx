import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "leaflet/dist/leaflet.css";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://radar.brunozilio.com"),
  applicationName: "Monitoramento",
  title: {
    default: "Monitoramento",
    template: "%s | Rio Taquari",
  },
  description:
    "Níveis dos rios, chuva acumulada, radar, satélite e barragens da Bacia do Rio Taquari-Antas.",
  keywords: [
    "Rio Taquari",
    "Bacia Taquari-Antas",
    "Muçum",
    "monitoramento hidrológico",
    "chuva",
    "radar meteorológico",
  ],
  alternates: {
    canonical: "/",
  },
  manifest: "/manifest.webmanifest",
  icons: {
    icon: [
      { url: "/favicon.svg", type: "image/svg+xml" },
      { url: "/icon-192.png", sizes: "192x192", type: "image/png" },
    ],
    shortcut: "/favicon.svg",
    apple: [
      {
        url: "/apple-touch-icon.png",
        sizes: "180x180",
        type: "image/png",
      },
    ],
    other: [
      {
        rel: "mask-icon",
        url: "/safari-pinned-tab.svg",
        color: "#1677ff",
      },
    ],
  },
  openGraph: {
    type: "website",
    locale: "pt_BR",
    url: "/",
    siteName: "Monitoramento",
    title: "Monitoramento",
    description:
      "Níveis dos rios, chuva acumulada, radar, satélite e barragens da Bacia do Rio Taquari-Antas.",
    images: [
      {
        url: "/og-monitoramento.png",
        width: 1200,
        height: 630,
        alt: "Monitoramento",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Monitoramento",
    description:
      "Níveis dos rios, chuva acumulada, radar, satélite e barragens da Bacia do Rio Taquari-Antas.",
    images: ["/og-monitoramento.png"],
  },
  other: {
    "msapplication-TileColor": "#1677ff",
  },
};

export const viewport: Viewport = {
  themeColor: "#f7f7f4",
  colorScheme: "light",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        {children}
      </body>
    </html>
  );
}
