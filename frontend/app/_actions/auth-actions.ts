"use server";

import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";

export async function getAuthenticatedUserId() {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    throw new Error("Not authenticated");
  }
  return session.user.id;
}

export async function withAuth<T>(action: (userId: string) => Promise<T>): Promise<T> {
  const userId = await getAuthenticatedUserId();
  return action(userId);
}
