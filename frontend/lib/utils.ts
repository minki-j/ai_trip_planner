import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

import { Session } from "next-auth";

export function returnWebSockerURL(
  session: Session | null,
  endpoint?: string
): URL {
  if (!endpoint) {
    throw new Error("Endpoint is empty");
  }

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
  if (!backendUrl) {
    throw new Error("Backend URL is not configured");
  }

  const backendUrlObj = new URL(backendUrl);
  const wsProtocol = backendUrlObj.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = new URL(`/ws/${endpoint}`, backendUrlObj.href);

  wsUrl.protocol = wsProtocol;
  wsUrl.searchParams.set("user_id", session?.user?.id || "");

  return wsUrl;
};

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
