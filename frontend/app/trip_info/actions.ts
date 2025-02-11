"use server";

import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";

import { formatLocalTime } from "@/lib/utils";

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

export async function updateTrip(formData: Record<string, any>) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    throw new Error("Not authenticated");
  }
  formData["id"] = session.user.id;

  const localized_trip_fixed_schedules = JSON.parse(
    formData["trip_fixed_schedules"]
  ).map((s: any) => {
    s.time = {
      start_time: formatLocalTime(s.time.start_time),
      end_time: s.time.end_time && formatLocalTime(s.time.end_time),
    };
    return s;
  });

  formData["trip_fixed_schedules"] = JSON.stringify(
    localized_trip_fixed_schedules
  );

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
