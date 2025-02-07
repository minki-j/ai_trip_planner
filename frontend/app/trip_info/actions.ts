"use server";

import { client } from "@/lib/mongodb";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";
import { revalidatePath } from "next/cache";

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;

export async function getUserInfo() {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    throw new Error("Not authenticated");
  }
  try {
    const response = await fetch(
      `${backendUrl}/user_info?user_id=${session.user.id}`,
      {
        method: "GET",
      }
    );
    if (!response.ok) {
      throw new Error("Network response was not ok");
    }
    const state = await response.json();
    // console.log("state: ", state);
    return state;
  } catch (error) {
    console.error(error);
    return null;
  }
}

export async function updateTrip(formData: Record<string, any>) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    throw new Error("Not authenticated");
  }
  formData["id"] = session.user.id;

  const response = await fetch(
    `${backendUrl}/update_trip?user_id=${session.user.id}`,
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
