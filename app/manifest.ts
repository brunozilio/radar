import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Monitoramento",
    short_name: "Rio Taquari",
    description:
      "Monitoramento hidrometeorológico da Bacia do Rio Taquari-Antas.",
    id: "/",
    start_url: "/",
    display: "standalone",
    background_color: "#f7f7f4",
    theme_color: "#1677ff",
    lang: "pt-BR",
    icons: [
      {
        src: "/icon-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
  };
}
