const dateTime = new Intl.DateTimeFormat("id-ID", {
  dateStyle: "medium",
  timeStyle: "short",
});

const rupiah = new Intl.NumberFormat("id-ID", {
  style: "currency",
  currency: "IDR",
  maximumFractionDigits: 0,
});

export function formatDateTime(iso: string): string {
  return dateTime.format(new Date(iso));
}

export function formatRupiah(value: number): string {
  return rupiah.format(value);
}

export const TRIP_STATUS_LABEL = {
  published: "Dibuka",
  ongoing: "Berlangsung",
  completed: "Selesai",
  cancelled: "Dibatalkan",
} as const;

export const REQUEST_STATUS_LABEL = {
  pending: "Menunggu",
  accepted: "Diterima",
  rejected: "Ditolak",
  cancelled: "Dibatalkan",
} as const;
