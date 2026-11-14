import { useEffect, useRef, useState } from "react";
import { Map as MapLibreMap, Marker, NavigationControl, Popup } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

export type MapPosition = {
  location_id: string;
  latitude: number;
  longitude: number;
};

export type MapLocation = {
  id: string;
  name: string;
  category: string;
  latitude: number;
  longitude: number;
  description: string;
  distance_km: number;
};

type MapViewProps = {
  currentPosition: MapPosition;
  locations: MapLocation[];
};

function MapView({ currentPosition, locations }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const markersRef = useRef<Marker[]>([]);
  const [mapReady, setMapReady] = useState(false);

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
      center: [currentPosition.longitude, currentPosition.latitude],
      zoom: 13.5,
      minZoom: 10,
      maxZoom: 18,
      maxPitch: 0,
    });

    mapRef.current = map;
    map.addControl(new NavigationControl({ showCompass: false }), "top-right");
    map.on("load", () => setMapReady(true));

    return () => {
      markersRef.current.forEach((marker) => marker.remove());
      markersRef.current = [];
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!mapReady || !map) return;

    markersRef.current.forEach((marker) => marker.remove());
    const markers: Marker[] = [];

    const playerPopup = new Popup({ offset: 24 }).setText("Sua posição atual");
    const playerMarker = new Marker({ color: "#e7c875" })
      .setLngLat([currentPosition.longitude, currentPosition.latitude])
      .setPopup(playerPopup)
      .addTo(map);
    markers.push(playerMarker);

    locations
      .filter((location) => location.id !== currentPosition.location_id)
      .forEach((location) => {
        const popup = new Popup({ offset: 22 }).setText(
          location.name + " · " + location.distance_km.toFixed(2) + " km",
        );
        const marker = new Marker({ color: "#b8d78b" })
          .setLngLat([location.longitude, location.latitude])
          .setPopup(popup)
          .addTo(map);
        markers.push(marker);
      });

    markersRef.current = markers;
    map.flyTo({
      center: [currentPosition.longitude, currentPosition.latitude],
      zoom: 13.5,
      duration: 650,
    });
  }, [mapReady, currentPosition, locations]);

  return (
    <div
      ref={containerRef}
      className="maplibre-container"
      role="region"
      aria-label="Mapa de exploração com posição do personagem e locais descobertos"
    />
  );
}

export default MapView;
