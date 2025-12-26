import { create } from "zustand";

type Coordinates = {
  latitude: number;
  longitude: number;
  accuracy?: number;
};

type LocationStatus = "idle" | "prompting" | "granted" | "denied" | "error" | "unsupported";

type LocationState = {
  coords?: Coordinates;
  status: LocationStatus;
  error?: string;
  setCoords: (coords: Coordinates) => void;
  setStatus: (status: LocationStatus, error?: string) => void;
};

function loadStoredCoords(): Coordinates | undefined {
  if (typeof window === "undefined") return undefined;
  const raw = localStorage.getItem("vaadeh_location");
  if (!raw) return undefined;
  try {
    return JSON.parse(raw) as Coordinates;
  } catch {
    return undefined;
  }
}

const storedCoords = loadStoredCoords();

export const useLocationStore = create<LocationState>((set) => ({
  coords: storedCoords,
  status: storedCoords ? "granted" : "idle",
  error: undefined,
  setCoords: (coords) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("vaadeh_location", JSON.stringify(coords));
    }
    set({ coords, status: "granted", error: undefined });
  },
  setStatus: (status, error) => set({ status, error }),
}));
