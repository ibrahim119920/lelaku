import type { LatLng } from "./types";

// Nominatim (OpenStreetMap), gratis. Dipanggil hanya saat submit form, bukan per ketikan,
// sesuai usage policy mereka (maks 1 request/detik).
export async function geocode(query: string): Promise<LatLng> {
  const url = new URL("https://nominatim.openstreetmap.org/search");
  url.searchParams.set("format", "json");
  url.searchParams.set("limit", "1");
  url.searchParams.set("countrycodes", "id");
  url.searchParams.set("q", query);

  let results: { lat: string; lon: string }[];
  try {
    const response = await fetch(url, { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error();
    results = await response.json();
  } catch {
    throw new Error("Gagal mencari lokasi. Coba lagi sebentar lagi.");
  }

  const first = results[0];
  if (!first) throw new Error(`Lokasi "${query}" tidak ditemukan.`);
  return { lat: Number(first.lat), lng: Number(first.lon) };
}
