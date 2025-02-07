"use server";

import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";


const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;

export async function getGraphState() {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    throw new Error("Not authenticated");
  }
  try {
    const response = await fetch(
      `${backendUrl}/graph_state?user_id=${session.user.id}`,
      {
        method: "GET",
      }
    );
    if (!response.ok) {
      throw new Error("Network response was not ok");
    }
    const state = await response.json();
    return state;
  } catch (error) {
    console.error(error);
    return null;
  }
}

export async function updateSchedule(formData: Record<string, any>) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    throw new Error("Not authenticated");
  }
  formData["id"] = session.user.id;

  const response = await fetch(
    `${backendUrl}/update_schedule?user_id=${session.user.id}`,
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
  } else {
    return true;
  }
}
