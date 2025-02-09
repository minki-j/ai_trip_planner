"use client";

import { useState, useEffect } from "react";
import { redirect } from "next/navigation";
import ReactMarkdown from "react-markdown";

import { useSession } from "next-auth/react";

import ScheduleForm from "./schedule-form";
import ScheduleDisplay from "./schedule-display";

import { useToast } from "@/components/ui/use-toast";
import { Button } from "@/components/ui/button";
import { returnWebSockerURL } from "@/lib/utils";
import { resetAgentStateAction } from "./actions";

import { ScheduleItem } from "@/models/Schedule";

import { getGraphState } from "./actions";

interface ReasoningStep {
  title: string;
  description: string;
}

interface ProfilePageClientProps {
  initialActivities: any;
}
export default function ProfilePageClient() {
  const { data: session, status } = useSession();
  const [activities, setActivities] = useState<ScheduleItem[]>([]);
  const [reasoningSteps, setReasoningSteps] = useState<ReasoningStep[]>([]);
  const [isEditMode, setIsEditMode] = useState(false);

  useEffect(() => {
    const fetchInitialActivities = async () => {
      const initialActivities = await getGraphState();
      setActivities(initialActivities);
    };

    fetchInitialActivities();
  }, []);

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
        setReasoningSteps((prevSteps) => [response, ...prevSteps]);
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

  return (
    <div className="container mx-auto py-8 max-w-2xl px-4">
      {activities.length > 0 ? (
        <div className="relative">
          <button
            onClick={() => setIsEditMode(!isEditMode)}
            className="fixed top-20 right-4 w-12 h-10 bg-primary hover:bg-primary/90 text-white rounded-full flex items-center justify-center shadow-lg z-50 transition-all duration-200 hover:scale-105"
            aria-label={
              isEditMode ? "Switch to display mode" : "Switch to edit mode"
            }
          >
            {isEditMode ? "Display Mode" : "Edit Mode"}
          </button>
          {isEditMode ? (
            <ScheduleForm initialActivities={activities} />
          ) : (
            <ScheduleDisplay activities={activities} />
          )}
        </div>
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
