"use server";

import { unstable_cache } from "next/cache";
import { withAuth } from "./auth-actions";

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;

export async function getGraphState() {
  return withAuth(async (userId) => {
    return unstable_cache(
      async () => {
        try {
          const response = await fetch(
            `${backendUrl}/graph_state?user_id=${userId}`,
            {
              method: "GET",
            }
          );
          return response.json();
        } catch (error) {
          console.error(error);
          return null;
        }
      },
      [`graph-state-${userId}`],
      {
        revalidate: 120, // 2 minutes
        tags: [`user-${userId}`],
      }
    )();
  });
}
