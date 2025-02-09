import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";
import { redirect } from "next/navigation";

import { TripForm } from "./trip-form";
import { User } from "@/models/User";
import { getGraphState } from "./actions";

export default async function ProfilePage() {
  const session = await getServerSession(authOptions);

  if (!session || !session.user) {
    redirect("/");
  }

  const state = await getGraphState();

  if (!state) {
    return (
      <div className="container mx-auto py-8">
        <p className="text-muted-foreground">No user found</p>
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
    trip_accomodation_location: state.trip_accomodation_location,
    
    trip_budget: state.trip_budget,
    trip_theme: state.trip_theme,
    trip_fixed_schedules: state.trip_fixed_schedules,
  };

  return (
    <div className="container mx-auto py-8 max-w-2xl px-4">
      {/* <h1 className="text-xl font-bold mb-6">Trip Information</h1> */}
      <TripForm user={user} />
    </div>
  );
}
