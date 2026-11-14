import { useEffect, useRef } from "react";
import { Map as MapLibreMap, NavigationControl } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

const INITIAL_VIEW: [number, number] = [-46.6333, -23.5505];

function MapView() {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const map = new MapLibreMap({
      container: containerRef.current,
      style: {
        version: 8,
        sources: {
          openstreetmap: {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution: "© OpenStreetMap contributors",
          },
        },
        layers: [{ id: "openstreetmap-raster", type: "raster", source: "openstreetmap" }],
      },
      center: INITIAL_VIEW,
      zoom: 9.5,
      minZoom: 8,
      maxZoom: 17,
      maxPitch: 0,
    });

    map.addControl(new NavigationControl({ showCompass: false }), "top-right");

    return () => map.remove();
  }, []);

  return (
    <div
      ref={containerRef}
      className="maplibre-container"
      role="region"
      aria-label="Mapa cartográfico de referência da região metropolitana de São Paulo"
    />
  );
}

export default MapView;
