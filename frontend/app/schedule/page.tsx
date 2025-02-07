import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";
import { redirect } from "next/navigation";
import { getGraphState } from "./actions";
import ScheduleForm from "./schedule-form";

export default async function ProfilePage() {
  const session = await getServerSession(authOptions);

  if (!session || !session.user) {
    redirect("/");
  }

  // const state = await getGraphState();
  const state = {
    list_of_activities: [
      // {
      //   activity_id: "1",
      //   activity_name: "Visit the White House",
      //   activity_type: "Historic place",
      //   activity_start_time: "09:00",
      //   activity_end_time: "12:00",
      //   activity_location: "The White House",
      //   activity_budget: "$100",
      //   activity_description: "Visit the White House",
      // },
      // {
      //   activity_id: "1",
      //   activity_name: "Visit the White House",
      //   activity_type: "Historic place",
      //   activity_start_time: "09:00",
      //   activity_end_time: "12:00",
      //   activity_location: "The White House",
      //   activity_budget: "$100",
      //   activity_description: "Visit the White House",
      // },
    ],
  };

  if (!state) {
    return (
      <div className="container mx-auto py-8">
        <p className="text-muted-foreground">No user found</p>
      </div>
    );
  }

  interface Activity {
    activity_id: string;
    activity_name: string;
    activity_type: string;
    activity_start_time: string;
    activity_end_time: string;
    activity_location: string;
    activity_budget: string;
    activity_description: string;
  }

  interface Schedule {
    list_of_activities: Activity[];
  }
  const schedule: Schedule = {
    list_of_activities: state.list_of_activities,
  };

  return (
    <div className="container mx-auto py-8 max-w-2xl px-4">
      <h1 className="text-xl font-bold mb-6">Trip Schedule</h1>
      {schedule.list_of_activities.length > 0 ? (
        <ScheduleForm initialActivities={schedule.list_of_activities} />
      ) : (
          <p>No activities to display</p>
          
      )}
    </div>
  );
}
