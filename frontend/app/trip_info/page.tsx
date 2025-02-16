import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";
import { redirect } from "next/navigation";

import { TripForm } from "./trip-form";
import { User } from "@/models/User";
import { getGraphState } from "../_actions/graph-actions";

export default async function TripInfoPage() {
  const session = await getServerSession(authOptions);

  if (!session || !session.user) {
    redirect("/");
  }

  const state = await getGraphState();

  if (!state) {
    return (
      <div className="container mx-auto mt-[100px] px-8 flex flex-col items-center justify-center space-y-4 text-center">
        <div className="w-16 h-16 text-muted-foreground">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
            />
          </svg>
        </div>
        <h2 className="text-lg font-semibold">Trip Information Not Found</h2>
        <p className="text-sm text-muted-foreground max-w-md">
          We couldn't find your trip information. This might happen if your
          session has expired or if there was an error loading your information.
        </p>
        <a
          href="/"
          className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          Return to Home
        </a>
      </div>
    );
  }
  if (state.connection_closed) {
    return (
      <div className="container mx-auto mt-[100px] px-8 flex flex-col items-start justify-center space-y-4 text-start">
        <p>
          While the assistant is generating your schedule, you can't modify your trip
          information.
        </p>
        <p />
        Please wait a moment and try again later.
        <p />
      </div>
    );
  }

  const user: User = {
    id: state.user_id,
    googleId: state.googleId,
    user_name: state.user_name,
    user_interests: state.user_interests,
    user_extra_info: state.user_extra_info,

    trip_arrival_date: state.trip_arrival_date,
    trip_arrival_time: state.trip_arrival_time,
    trip_arrival_terminal: state.trip_arrival_terminal,

    trip_departure_date: state.trip_departure_date,
    trip_departure_time: state.trip_departure_time,
    trip_departure_terminal: state.trip_departure_terminal,

    trip_start_of_day_at: state.trip_start_of_day_at,
    trip_end_of_day_at: state.trip_end_of_day_at,

    trip_location: state.trip_location,
    trip_accommodation_location: state.trip_accommodation_location,

    trip_budget: state.trip_budget,
    trip_theme: state.trip_theme,
    trip_fixed_schedules: state.trip_fixed_schedules,
  };

  return (
    <div className="container mx-auto py-4 mt-[60px] max-w-2xl px-4">
      <TripForm user={user} />
    </div>
  );
}
