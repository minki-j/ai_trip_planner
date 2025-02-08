"use client";

import { useState } from "react";
import { redirect } from "next/navigation";
import ReactMarkdown from "react-markdown";

import { useSession } from "next-auth/react";

import ScheduleForm from "./schedule-form";

import { useToast } from "@/components/ui/use-toast";
import { Button } from "@/components/ui/button";
import { returnWebSockerURL } from "@/lib/utils";
import { resetAgentStateAction } from "./actions";

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

interface ReasoningStep {
  title: string;
  description: string;
}

interface ProfilePageClientProps {
  initialActivities: any;
}
export default function ProfilePageClient({
  initialActivities,
}: ProfilePageClientProps) {
  const { data: session, status } = useSession();

  const [activities, setActivities] = useState<Activity[]>(initialActivities);
  const [reasoningSteps, setReasoningSteps] = useState<ReasoningStep[]>([]);

  const { toast } = useToast();

  const connectWebSocket = async () => {
    let websocket: WebSocket;
    try {
      if (!session?.user?.id) {
        throw new Error("session user id is null");
      }
      const wsUrl = returnWebSockerURL("generate_schedule");
      wsUrl.searchParams.set("user_id", session?.user?.id);

      websocket = new WebSocket(wsUrl.toString());

      websocket.onerror = (error) => {
        console.error("WebSocket error:", error);
        toast({
          title: "Connection Error",
          description: "WebSocket connection failed",
          variant: "destructive",
          duration: 4000,
        });
      };
    } catch (error) {
      console.error("Failed to connect to WebSocket:", error);
      toast({
        title: "Error",
        description: "Failed to connect to WebSocket",
        variant: "destructive",
        duration: 4000,
      });
      return;
    }
    return websocket;
  };

  const startGeneration = async () => {
    const websocket = await connectWebSocket();
    if (!websocket) {
      return;
    }

    try {
      await Promise.race([
        new Promise((resolve, reject) => {
          websocket.onopen = resolve;
          websocket.onerror = reject;
        }),
        new Promise((_, reject) =>
          setTimeout(
            () => reject(new Error("WebSocket Connection timeout")),
            5000
          )
        ),
      ]);

      websocket.onmessage = async (event) => {
        const response = JSON.parse(event.data);
        // console.log("WebSocket response: ", response);
        if (!response) return;
        if (response.error) {
          console.error("Error:", response.error);
          toast({
            title: "Error",
            description: response.error,
            variant: "destructive",
            duration: 4000,
          });
          return;
        }
        setReasoningSteps((prevSteps) => [...prevSteps, response]);
      };
    } catch (error: any) {
      if (websocket.readyState !== WebSocket.CLOSED) {
        websocket.close();
      }
      toast({
        title: "Error",
        description: `${
          error.message ? error.message : "Sorry something went wrong"
        }`,
        variant: "destructive",
        duration: 4000,
      });
    }
  };

  const resetAgentState = () => {
    resetAgentStateAction();
    setActivities([]);
    setReasoningSteps([]);
  };

  // setActivities([
  //     {
  //       activity_id: "1",
  //       activity_name: "Visit the White House",
  //       activity_type: "Historic place",
  //       activity_start_time: "09:00",
  //       activity_end_time: "12:00",
  //       activity_location: "The White House",
  //       activity_budget: "$100",
  //       activity_description: "Visit the White House",
  //     },
  //     {
  //       activity_id: "1",
  //       activity_name: "Visit the White House",
  //       activity_type: "Historic place",
  //       activity_start_time: "09:00",
  //       activity_end_time: "12:00",
  //       activity_location: "The White House",
  //       activity_budget: "$100",
  //       activity_description: "Visit the White House",
  //     },
  //   ]);

  return (
    <div className="container mx-auto py-8 max-w-2xl px-4">
      {activities.length > 0 ? (
        <ScheduleForm initialActivities={activities} />
      ) : (
        <>
          {reasoningSteps.length > 0 ? (
            <div className="flex flex-col items-start justify-start space-y-4">
              {reasoningSteps.map((step, index) => (
                <div
                  key={index}
                  className="flex flex-col items-start justify-start space-y-1"
                >
                  <p className="text-s font-bold">{step.title}</p>
                  <ReactMarkdown
                    components={{
                      p: ({ node, children }) => (
                        <p className="my-2">{children}</p>
                      ),
                      ul: ({ node, children }) => (
                        <ul className="list-disc pl-4 space-y-1">{children}</ul>
                      ),
                      ol: ({ node, children }) => (
                        <ol className="list-decimal pl-4 space-y-1">
                          {children}
                        </ol>
                      ),
                    }}
                    className="text-xs prose prose-sm max-w-none prose-neutral dark:prose-invert"
                  >
                    {step.description}
                  </ReactMarkdown>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center space-y-4 ">
              <p>No activities to display</p>
              <Button onClick={startGeneration}>Start Generation</Button>
              <Button onClick={resetAgentState}>Reset Agent State</Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
