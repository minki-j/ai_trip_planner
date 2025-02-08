import { getServerSession } from "next-auth/next";
import { redirect } from "next/navigation";
import { authOptions } from "@/lib/auth";
import { getGraphState } from "./actions";
import ProfilePageClient from "./page-client";

export default async function ProfilePageServer() {
  const session = await getServerSession(authOptions);
  
  if (!session || !session.user) {
    redirect("/");
  }

  let initialActivities = await getGraphState()
  initialActivities = initialActivities?.activities || [];

  return <ProfilePageClient initialActivities={initialActivities} />;
}
