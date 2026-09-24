import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    data: [],
    message: "Daftar permintaan siap diimplementasikan.",
  });
}

export async function POST(request: Request) {
  const payload = await request.json();

  return NextResponse.json(
    { data: payload, message: "Permintaan bergabung berhasil diterima." },
    { status: 201 },
  );
}
