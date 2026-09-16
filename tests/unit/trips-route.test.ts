import { describe, expect, it } from "vitest";

import { GET, POST } from "../../src/app/api/trips/route";

describe("trips API route", () => {
  it("returns the current trip collection and echoes accepted trip data", async () => {
    const listResponse = await GET();

    expect(listResponse.status).toBe(200);
    await expect(listResponse.json()).resolves.toEqual({
      data: [],
      message: "Daftar perjalanan siap diimplementasikan.",
    });

    const trip = {
      destination: "Yogyakarta",
      departureDate: "2026-10-01",
    };
    const createResponse = await POST(
      new Request("http://localhost/api/trips", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(trip),
      }),
    );

    expect(createResponse.status).toBe(201);
    await expect(createResponse.json()).resolves.toEqual({
      data: trip,
      message: "Perjalanan berhasil diterima.",
    });
  });
});
