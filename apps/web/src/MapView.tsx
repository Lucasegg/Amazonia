import { useEffect, useRef } from "react";
import {
  Map as MapLibreMap,
  NavigationControl,
  Popup,
  type GeoJSONSource,
} from "maplibre-gl";
import type { Feature, FeatureCollection, Point, Polygon } from "geojson";
import "maplibre-gl/dist/maplibre-gl.css";
import type { MapCell, MapData, MapPOI } from "./types";

const INITIAL_VIEW: [number, number] = [-46.6333, -23.5505];

type CellProperties = Pick<MapCell, "q" | "r" | "discovered" | "current" | "adjacent">;
type PoiProperties = Pick<MapPOI, "id" | "name" | "category" | "cell_q" | "cell_r">;

function cellsToGeoJSON(cells: MapCell[]): FeatureCollection<Polygon, CellProperties> {
  const features: Feature<Polygon, CellProperties>[] = cells.map((cell) => {
    const ring: [number, number][] = [];
    for (let index = 0; index < 6; index += 1) {
      const angle = (Math.PI / 3) * index + Math.PI / 6;
      const east = cell.radius_meters * Math.cos(angle);
      const north = cell.radius_meters * Math.sin(angle);
      const latitude = cell.latitude + north / 111_320;
      const longitude = cell.longitude + east / (111_320 * Math.cos((cell.latitude * Math.PI) / 180));
      ring.push([longitude, latitude]);
    }
    ring.push(ring[0]);
    return {
      type: "Feature",
      properties: {
        q: cell.q,
        r: cell.r,
        discovered: cell.discovered,
        current: cell.current,
        adjacent: cell.adjacent,
      },
      geometry: { type: "Polygon", coordinates: [ring] },
    };
  });
  return { type: "FeatureCollection", features };
}

function poisToGeoJSON(pois: MapPOI[]): FeatureCollection<Point, PoiProperties> {
  return {
    type: "FeatureCollection",
    features: pois.map((poi) => ({
      type: "Feature",
      properties: {
        id: poi.id,
        name: poi.name,
        category: poi.category,
        cell_q: poi.cell_q,
        cell_r: poi.cell_r,
      },
      geometry: {
        type: "Point",
        coordinates: [poi.longitude, poi.latitude],
      },
    })),
  };
}

type MapViewProps = {
  mapData: MapData | null;
  onMove: (q: number, r: number) => void;
};

function MapView({ mapData, onMove }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const mapDataRef = useRef(mapData);
  const onMoveRef = useRef(onMove);
  mapDataRef.current = mapData;
  onMoveRef.current = onMove;

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
      center: mapDataRef.current
        ? [mapDataRef.current.player_position.longitude, mapDataRef.current.player_position.latitude]
        : INITIAL_VIEW,
      zoom: 11.5,
      minZoom: 9,
      maxZoom: 17,
      maxPitch: 0,
    });
    mapRef.current = map;
    map.addControl(new NavigationControl({ showCompass: false }), "top-right");

    map.on("load", () => {
      map.addSource("game-cells", {
        type: "geojson",
        data: cellsToGeoJSON(mapDataRef.current?.cells ?? []),
      });
      map.addLayer({
        id: "game-cells-fill",
        type: "fill",
        source: "game-cells",
        paint: {
          "fill-color": [
            "case",
            ["boolean", ["get", "current"], false], "#b8d78b",
            ["boolean", ["get", "discovered"], false], "#6e8e5d",
            "#24352a",
          ],
          "fill-opacity": [
            "case",
            ["boolean", ["get", "current"], false], 0.58,
            ["boolean", ["get", "discovered"], false], 0.38,
            0.16,
          ],
        },
      });
      map.addLayer({
        id: "game-cells-outline",
        type: "line",
        source: "game-cells",
        paint: {
          "line-color": "#c8dda9",
          "line-width": ["case", ["boolean", ["get", "current"], false], 2.5, 1.2],
          "line-opacity": 0.9,
        },
      });

      map.addSource("game-pois", {
        type: "geojson",
        data: poisToGeoJSON(mapDataRef.current?.points_of_interest ?? []),
      });
      map.addLayer({
        id: "game-pois-points",
        type: "circle",
        source: "game-pois",
        paint: {
          "circle-radius": 6,
          "circle-color": "#f2cf78",
          "circle-stroke-color": "#172117",
          "circle-stroke-width": 2,
        },
      });
      map.on("click", "game-pois-points", (event) => {
        const name = event.features?.[0]?.properties?.name;
        if (typeof name !== "string") return;
        new Popup({ offset: 10 }).setLngLat(event.lngLat).setText(name).addTo(map);
      });
      map.on("mouseenter", "game-pois-points", () => {
        map.getCanvas().style.cursor = "help";
      });
      map.on("mouseleave", "game-pois-points", () => {
        map.getCanvas().style.cursor = "";
      });

      map.on("click", "game-cells-fill", (event) => {
        const properties = event.features?.[0]?.properties;
        if (!properties || !properties.adjacent || properties.current) return;
        onMoveRef.current(Number(properties.q), Number(properties.r));
      });
      map.on("mouseenter", "game-cells-fill", () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", "game-cells-fill", () => {
        map.getCanvas().style.cursor = "";
      });
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapData) return;
    const updateSources = () => {
      const cellsSource = map.getSource("game-cells") as GeoJSONSource | undefined;
      const poisSource = map.getSource("game-pois") as GeoJSONSource | undefined;
      cellsSource?.setData(cellsToGeoJSON(mapData.cells));
      poisSource?.setData(poisToGeoJSON(mapData.points_of_interest));
      map.easeTo({
        center: [mapData.player_position.longitude, mapData.player_position.latitude],
        duration: 350,
      });
    };
    if (map.isStyleLoaded() && map.getSource("game-cells") && map.getSource("game-pois")) {
      updateSources();
    } else {
      map.once("load", updateSources);
    }
  }, [mapData]);

  return (
    <div
      ref={containerRef}
      className="maplibre-container"
      role="region"
      aria-label="Mapa hexagonal com pontos de interesse descobertos"
    />
  );
}

export default MapView;
