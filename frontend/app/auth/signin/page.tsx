"use client";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { PenLine } from "lucide-react";
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
      <Card className="w-full max-w-md p-8">
        <div className="text-center space-y-6">
          <div className="flex justify-center">
            <PenLine className="h-12 w-12 text-primary" />
          </div>
          <h1 className="text-2xl font-bold">Welcome to AI Tour Assistant</h1>
          <p className="text-muted-foreground">
            Sign in to start planning your trip!
          </p>
          <div className="space-y-2">
            <Button className="w-full" onClick={() => signIn("google")}>
              Sign in with Google
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
