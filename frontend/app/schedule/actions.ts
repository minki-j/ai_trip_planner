"use server";

import { withAuth } from "../_actions/auth-actions";
import { revalidateTag } from "next/cache";

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;

export async function updateSchedule(formData: Record<string, any>) {
  return withAuth(async (userId) => {
    formData["id"] = userId;

    const response = await fetch(
      `${backendUrl}/update_schedule?user_id=${userId}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      }
    );
    if (!response.ok) {
      throw new Error("Network response was not ok");
    }
    revalidateTag(`user-${userId}`);
    return true;
  });
}

export async function resetAgentStateAction() {
  return withAuth(async (userId) => {
    const response = await fetch(
      `${backendUrl}/reset_state?user_id=${userId}`,
      {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );
    if (!response.ok) {
      throw new Error("Network response was not ok");
    }

    // Revalidate the graph state cache
    revalidateTag(`user-${userId}`);
    return true;
  });
}
