import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Lelaku",
    short_name: "Lelaku",
    description: "Platform berbagi perjalanan dan teman seperjalanan.",
    start_url: "/",
    display: "standalone",
    background_color: "#f8fafc",
    theme_color: "#0f766e",
  };
}
