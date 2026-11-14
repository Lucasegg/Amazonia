export type MapCell = {
  q: number;
  r: number;
  latitude: number;
  longitude: number;
  radius_meters: number;
  discovered: boolean;
  current: boolean;
  adjacent: boolean;
};

export type MapPOI = {
  id: string;
  name: string;
  category: string;
  latitude: number;
  longitude: number;
  description: string;
  cell_q: number;
  cell_r: number;
};

export type MapData = {
  campaign_id: string;
  world_time_minutes: number;
  player_position: {
    q: number;
    r: number;
    latitude: number;
    longitude: number;
  };
  hex_radius_meters: number;
  cells: MapCell[];
  points_of_interest: MapPOI[];
};
