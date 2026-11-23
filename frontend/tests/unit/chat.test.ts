import { describe, expect, it } from "vitest";

import { isChatParticipant, mergeMessages } from "../../src/lib/chat";
import type { Message, TripMember } from "../../src/lib/api/types";

function message(id: string): Message {
  return {
    message_id: id,
    trip_id: "trip-1",
    sender_id: "user-1",
    sender_name: "Naya",
    content: `pesan ${id}`,
    sent_at: "2026-11-23T10:00:00Z",
  };
}

function member(userId: string, status: string): TripMember {
  return {
    user_id: userId,
    name: userId,
    profile_photo: null,
    role: "passenger",
    trip_member_id: `tm-${userId}`,
    status,
  };
}

describe("mergeMessages", () => {
  it("menggabungkan pesan baru tanpa duplikat", () => {
    const first = message("1");
    const second = message("2");
    expect(mergeMessages([first], [first, second])).toEqual([first, second]);
  });

  it("tidak mengubah referensi kalau tidak ada pesan baru", () => {
    const first = message("1");
    const current = [first];
    expect(mergeMessages(current, [])).toBe(current);
    expect(mergeMessages(current, [first])).toBe(current);
  });
});

describe("isChatParticipant", () => {
  it("driver selalu boleh chat", () => {
    expect(isChatParticipant("driver-1", "driver-1", null)).toBe(true);
  });

  it("passenger active boleh chat", () => {
    expect(isChatParticipant("user-2", "driver-1", [member("user-2", "active")])).toBe(true);
  });

  it("passenger cancelled tidak boleh chat", () => {
    expect(isChatParticipant("user-2", "driver-1", [member("user-2", "cancelled")])).toBe(false);
  });

  it("pengguna di luar trip tidak boleh chat", () => {
    expect(isChatParticipant("user-3", "driver-1", [member("user-2", "active")])).toBe(false);
  });

  it("belum ada data anggota selain driver tidak boleh chat", () => {
    expect(isChatParticipant("user-2", "driver-1", null)).toBe(false);
  });
});
