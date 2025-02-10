"use client";

import { useState, useEffect, useRef } from "react";
import { redirect } from "next/navigation";
import { useSession } from "next-auth/react";

import { RefreshCw, Edit } from "lucide-react";
import ReactMarkdown from "react-markdown";

import ScheduleForm from "./schedule-form";
import ScheduleDisplay from "./schedule-display";
import Loading from "./loading";
import { getGraphState, resetAgentStateAction } from "./actions";

import { useToast } from "@/components/ui/use-toast";
import { Button } from "@/components/ui/button";
import { returnWebSockerURL } from "@/lib/utils";
import { ScheduleItem } from "@/models/Schedule";

interface ReasoningStep {
  title: string;
  description: string;
}

export default function SchedulePage() {
  const { data: session, status } = useSession();
  
  const [schedules, setSchedules] = useState<ScheduleItem[]>([]);
  const [reasoningSteps, setReasoningSteps] = useState<ReasoningStep[]>([]);
  
  const [isLoading, setIsLoading] = useState(true);
  const [isEditMode, setIsEditMode] = useState(false);
  const [showReasoningSteps, setShowReasoningSteps] = useState(true);
  
  const stepsContainerRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    if (stepsContainerRef.current && reasoningSteps.length > 0) {
      // stepsContainerRef.current.scrollTop = 0;
    }
  }, [reasoningSteps]);

  useEffect(() => {
    setIsLoading(true);
    const fetchInitialSchedules = async () => {
      const state = await getGraphState();
      setSchedules(state.schedule_list);
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
      return;
    }
    return websocket;
  };

  const startGeneration = async () => {
    await resetAgentStateAction();
    setReasoningSteps([]);
    setSchedules([]);

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
        console.log("WebSocket response: ", response);

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
          setSchedules((prevSchedules) => [...prevSchedules, response]);
        }
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

  if (isLoading) {
    return <Loading />;
  }

  return (
    <>
      {/* Reasoning Steps */}
      {reasoningSteps.length > 0 && showReasoningSteps && (
        <div 
          ref={stepsContainerRef}
          className="p-4 space-y-4 h-[30vh] overflow-y-scroll scrollbar-show bg-gray-100">
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
      )}

      {/* Show/Hide reasoning steps button */}
      {reasoningSteps.length > 0 ? (
        <button
          onClick={() => setShowReasoningSteps(!showReasoningSteps)}
          className="w-full py-1 flex justify-center items-center text-gray-500 bg-gray-200"
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
                showReasoningSteps ? "transform rotate-180" : ""
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
      ) : (
        <div className="w-full py-1 flex justify-center items-center text-white bg-gray-100">
          <span className="text-sm">No reasoning steps available</span>
        </div>
      )}

      <div className="container mx-auto max-w-3xl px-4">
        {/* Main content */}
        <div className="space-y-6">
          {schedules.length > 0 ? (
            <div className="bg-card rounded-lg pr-2">
              {isEditMode ? (
                <ScheduleForm initialSchedules={schedules} />
              ) : (
                <ScheduleDisplay schedules={schedules} />
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 bg-muted/50 rounded-lg mt-4">
              <p className="text-muted-foreground">No schedules to display</p>
            </div>
          )}
        </div>

        {/* Floating Buttons */}
        <Button
          onClick={() => {
            if (
              window.confirm(
                "Are you sure you want to regenerate a new schedule?"
              )
            ) {
              startGeneration();
            }
          }}
          size="lg"
          className="fixed bottom-3 right-3 rounded-full w-8 h-8 shadow-lg hover:shadow-xl transition-shadow duration-200 flex items-center justify-center p-0 bg-primary text-primary-foreground"
        >
          <RefreshCw className="h-4 w-4" />
        </Button>
        <Button
          onClick={() => setIsEditMode(!isEditMode)}
          size="lg"
          className="fixed bottom-14 right-3 rounded-full w-8 h-8 shadow-lg hover:shadow-xl transition-shadow duration-200 flex items-center justify-center p-0 bg-primary text-primary-foreground"
        >
          <Edit className="h-4 w-4" />
        </Button>
      </div>
    </>
  );
}
