export type AuthUser = {
  id: string;
  email: string;
  name?: string;
};

export async function getCurrentUser(): Promise<AuthUser | null> {
  // TODO: Hubungkan dengan mekanisme autentikasi yang dipilih.
  return null;
}
