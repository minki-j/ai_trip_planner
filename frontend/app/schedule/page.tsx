"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";

import ScheduleForm from "./schedule-form";
import ScheduleDisplay from "./schedule-display";
import Loading from "./loading";
import { resetAgentStateAction, revalidateSchedule } from "./actions";
import { getGraphState } from "../_actions/graph-actions";

import { useToast } from "@/components/ui/use-toast";
import { Button } from "@/components/ui/button";
import { returnWebSockerURL } from "@/lib/utils";
import { ScheduleItem } from "@/models/Schedule";

interface ReasoningStep {
  title: string;
  description: string;
}

export default function SchedulePage() {
  const router = useRouter();
  const { data: session, status } = useSession();

  const [schedules, setSchedules] = useState<ScheduleItem[]>([]);
  const [reasoningSteps, setReasoningSteps] = useState<ReasoningStep[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [isEditMode, setIsEditMode] = useState(false);
  const [showReasoningSteps, setShowReasoningSteps] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [connectionClosed, setConnectionClosed] = useState(false);
  const [timeLeft, setTimeLeft] = useState(5 * 60); // 5 minutes in seconds

  const stepsContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (connectionClosed && timeLeft > 0) {
      const timer = setInterval(() => {
        setTimeLeft((prevTime) => {
          if (prevTime <= 1) {
            clearInterval(timer);
            window.location.reload();
            return 0;
          }
          return prevTime - 1;
        });
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [connectionClosed, timeLeft]);

  useEffect(() => {
    if (schedules.length > 0 || reasoningSteps.length > 0) {
      setIsLoading(false);
    }
  }, [reasoningSteps, schedules]);

  useEffect(() => {
    setIsLoading(true);
    const fetchInitialSchedules = async () => {
      const state = await getGraphState();
      console.log("state: ", state);

      if (state) {
        if (state.connection_closed) {
          setConnectionClosed(true);
          return;
        }
        if (!state.trip_location) {
          toast({
            title: "Trip Information Not Found",
            description: "Please fill out your trip information.",
            variant: "destructive",
          });
          router.push("/trip_info");
        } else {
          setSchedules(state.schedule_list);
        }
      }
    };

    fetchInitialSchedules().finally(() => setIsLoading(false));
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
      window.location.reload();

      return;
    }
    return websocket;
  };

  const startGeneration = async () => {
    setIsLoading(true);
    await resetAgentStateAction();
    setReasoningSteps([]);
    setSchedules([]);
    setIsGenerating(true);

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

        if (response.data_type == "reasoning_steps") {
          setReasoningSteps((prevSteps) => [...prevSteps, response]);
        } else if (response.data_type == "schedule") {
          delete response.data_type;
          if (response.activity_type == "REMOVE") {
            setSchedules((prevSchedules) =>
              prevSchedules.filter((schedule) => schedule.id !== response.id)
            );
          } else {
            setSchedules((prevSchedules) => {
              const existingIndex = prevSchedules.findIndex(
                (schedule) => schedule.id === response.id
              );
              if (existingIndex !== -1) {
                // Replace existing schedule
                const updatedSchedules = [...prevSchedules];
                updatedSchedules[existingIndex] = response;
                return updatedSchedules;
              } else {
                // Add new schedule
                return [...prevSchedules, response];
              }
            });
          }
        }
      };

      websocket.onclose = async () => {
        await revalidateSchedule(session?.user?.id ?? "");
        setIsLoading(false);
        setIsGenerating(false);
        router.refresh();
      };
    } catch (error: any) {
      if (websocket.readyState !== WebSocket.CLOSED) {
        websocket.close();
      }
      setIsLoading(false);
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

  if (isLoading) {
    return <Loading />;
  }

  if (connectionClosed) {
    return (
      <div className="w-full mt-[60px] max-w-xl py-5 px-8 flex flex-col gap-3 justify-center items-start">
        <h1 className="text-lg font-bold">Streaming is not available</h1>
        <div className="text-md text-muted-foreground space-y-2">
          <p>The websocket connection to the server has been closed.</p>
          <p>
            We are currently working on creating your personalized schedule. While this process is happening behind the scenes, we're not able to show you the real-time progress yet.
          </p>
          <p>
            Please wait until the generation is complete. It may take up to 5
            minutes. Apologies for the inconvenience.
          </p>
        </div>
        <div className="mt-4 text-sm font-medium">
          Time remaining: {Math.floor(timeLeft / 60)}:
          {String(timeLeft % 60).padStart(2, "0")}
        </div>
      </div>
    );
  }

  return (
    <div className="container mt-[60px] mx-auto max-w-3xl">
      {/* Main content */}
      {schedules.length > 0 ? (
        <div>
          {isEditMode ? (
            <ScheduleForm initialSchedules={schedules} />
          ) : (
            <ScheduleDisplay
              schedules={schedules}
              startGeneration={startGeneration}
              setIsEditMode={setIsEditMode}
              isGenerating={isGenerating}
            />
          )}
        </div>
      ) : (
        <div className="w-full py-5 flex flex-col gap-3 justify-center items-center text-gray-600 bg-gray-50 rounded-b-lg border-t border-gray-100">
          <div className="flex items-center gap-2">
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span className="text-sm font-medium">
              No schedule generated yet
            </span>
          </div>
          <p className="text-sm text-gray-500 text-center">
            Click the button to create your personalized travel schedule
          </p>
          <Button
            onClick={() => {
              startGeneration();
            }}
            className="bg-blue-600 text-white text-sm font-medium"
          >
            Generate Schedule
          </Button>
        </div>
      )}

      {/* Reasoning Steps */}
      {/* {reasoningSteps.length > 0 && showReasoningSteps && (
        <div
          ref={stepsContainerRef}
          className="p-4 space-y-4 h-[30vh] overflow-y-scroll scrollbar-show bg-gray-100 sticky bottom-7"
        >
          {reasoningSteps.map((step, index) => (
            <div key={index} className="border-l-2 border-primary/20 pl-4 py-2">
              <h3 className="text-sm font-medium text-primary mb-2">
                {step.title}
              </h3>
              <ReactMarkdown
                components={{
                  p: ({ node, children }) => (
                    <p className="text-sm text-muted-foreground mb-2">
                      {children}
                    </p>
                  ),
                  ul: ({ node, children }) => (
                    <ul className="list-disc pl-4 space-y-1 text-sm text-muted-foreground">
                      {children}
                    </ul>
                  ),
                  ol: ({ node, children }) => (
                    <ol className="list-decimal pl-4 space-y-1 text-sm text-muted-foreground">
                      {children}
                    </ol>
                  ),
                }}
                className="prose prose-sm max-w-none prose-neutral dark:prose-invert"
              >
                {step.description}
              </ReactMarkdown>
            </div>
          ))}
        </div>
      )} */}

      {/* Show/Hide reasoning steps button */}
      {/* {reasoningSteps.length > 0 && (
        <button
          onClick={() => setShowReasoningSteps(!showReasoningSteps)}
          className="w-full py-1 flex justify-center items-center text-gray-500 bg-gray-200 sticky bottom-0"
          aria-label={
            showReasoningSteps ? "Hide reasoning steps" : "Show reasoning steps"
          }
        >
          <div className="flex items-center gap-2 text-sm">
            <span>
              {showReasoningSteps
                ? "Hide reasoning steps"
                : "Show reasoning steps"}
            </span>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
              className={`w-4 h-4 transition-transform ${
                showReasoningSteps ? "" : "transform rotate-180"
              }`}
            >
              <path
                fillRule="evenodd"
                d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
                clipRule="evenodd"
              />
            </svg>
          </div>
        </button>
      )} */}
    </div>
  );
}
