import { ExternalLink } from "lucide-react";

const CAMERAS = [
  {
    videoId: "kn1qx5Sin20",
    name: "Início do Rio Taquari",
    location: "Encontro dos rios Carreiro e Antas",
  },
  {
    videoId: "K7IAHQftZMk",
    name: "Ponte entre Muçum e Encantado",
    location: "Barra do Guaporé",
  },
] as const;

export default function LiveCameras() {
  return (
    <section
      className="panel cameras-panel"
      id="cameras-ao-vivo"
      aria-labelledby="cameras-title"
    >
      <div className="module-header">
        <div>
          <h2 id="cameras-title">Câmeras ao vivo</h2>
        </div>
      </div>
      <div className="cameras-grid">
        {CAMERAS.map((camera) => (
          <article className="camera-card" key={camera.videoId}>
            <div className="camera-player">
              <iframe
                src={`https://www.youtube.com/embed/${camera.videoId}?playsinline=1&hl=pt-BR`}
                title={`Câmera ao vivo: ${camera.name} — ${camera.location}`}
                width="560"
                height="315"
                loading="lazy"
                referrerPolicy="strict-origin-when-cross-origin"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                allowFullScreen
              />
            </div>
            <div className="camera-caption">
              <div>
                <h3>{camera.name}</h3>
                <p>{camera.location}</p>
              </div>
              <a
                href={`https://www.youtube.com/watch?v=${camera.videoId}`}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={`Abrir câmera ${camera.name} no YouTube (nova aba)`}
              >
                YouTube <ExternalLink size={14} aria-hidden="true" />
              </a>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
