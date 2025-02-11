import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';


export function returnWebSockerURL(
  endpoint: string
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
  
  return wsUrl;
};

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}


export function formatLocalTime(utcString: string) {
  const date = new Date(utcString);

  // Extract local year, month, day, hour, and minute
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0"); // Months are 0-based
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");

  return `${year}-${month}-${day} ${hours}:${minutes}`;
}