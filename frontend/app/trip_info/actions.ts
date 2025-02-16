"use server";

import { withAuth } from "../_actions/auth-actions";
import { formatLocalTime } from "@/lib/utils";
import { revalidateTag } from "next/cache";

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;

export async function updateTrip(formData: Record<string, any>) {
  return withAuth(async (userId) => {
    formData["id"] = userId;

    if (formData["trip_fixed_schedules"]) {
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
    } else {
      formData["trip_fixed_schedules"] = "[]";
    }

    const response = await fetch(
      `${backendUrl}/update_trip?user_id=${userId}`,
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
