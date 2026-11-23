import type { Message, TripMember } from "@/lib/api/types";

/** Gabungkan pesan baru tanpa duplikat, tetap urut dari yang paling lama. */
export function mergeMessages(prev: Message[], incoming: Message[]): Message[] {
  if (incoming.length === 0) return prev;

  const seen = new Set(prev.map((message) => message.message_id));
  const fresh = incoming.filter((message) => !seen.has(message.message_id));
  return fresh.length === 0 ? prev : [...prev, ...fresh];
}

/** Driver atau passenger dengan member status `active` boleh membuka chat. */
export function isChatParticipant(
  currentUserId: string,
  driverId: string,
  members: TripMember[] | null | undefined,
): boolean {
  if (currentUserId === driverId) return true;
  return (
    members?.some(
      (member) => member.user_id === currentUserId && member.status === "active",
    ) ?? false
  );
}
