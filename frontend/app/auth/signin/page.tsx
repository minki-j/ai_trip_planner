"use client";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Bus, Plane } from "lucide-react";
import { signIn } from "next-auth/react";
import { useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/ui/use-toast";

export default function SignIn() {
  const { data: session, status, update } = useSession();
  const router = useRouter();
  const { toast } = useToast();

  useEffect(() => {
    if (status === "authenticated") {
      router.push("/");
    }
  }, [status, router]);

  return (
    <div className="min-h-[80vh] px-6 flex items-center justify-center">
      <Card className="w-full max-w-md p-8 border-0">
        <div className="text-center space-y-3">
          <div className="flex justify-center gap-3">
            <Bus className="h-12 w-12 text-primary" />
            <Plane className="h-12 w-12 text-primary" />
          </div>
          <h1 className="text-xl font-bold pb-3">
            Welcome to
            <br />
            AI Trip Planner
          </h1>
          <p className="text-md text-muted-foreground">
            Start planning your trip
          </p>
          <div className="space-y-2">
            <Button className="text-sm w-full" onClick={() => signIn("google")}>
              Sign in with Google
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
