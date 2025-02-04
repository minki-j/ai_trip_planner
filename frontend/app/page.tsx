"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import { redirect } from "next/navigation";

import ChatContainer from "../components/ChatContainer";
import { useToast } from "@/components/ui/use-toast";
import { Message } from "@/types/types";
import { returnWebSockerURL } from "@/lib/utils";

import { Role } from "@/types/types";

const first_message =
  "Hi, I'm your tour assistant! May I introduce how this tour assistant works?";

export default function Home() {
  const { data: session, status } = useSession();
  const [messages, setMessages] = useState<Message[]>([
    {
      message: first_message,
      sentTime: new Date().toISOString(),
      sender: Role.Assistant,
    },
  ]);
  const { toast } = useToast();

  if (status === "loading") {
    return (
      <div className="flex items-center justify-center min-h-[80vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (status === "unauthenticated") {
    redirect("/auth/signin");
  }

  const connectWebSocket = () => {
    let websocket: WebSocket;
    try {
      const wsUrl = returnWebSockerURL(session, "chat");
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

  const assignOnMessageHanlder = async (websocket: WebSocket) => {
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

      setMessages((prevMessages) => [
        ...prevMessages,
        {
          message: response.message,
          sender: response.role,
          sentTime: new Date().toISOString(),
        },
      ]);
    };
  };

  const onSendMessage = async (message: Message) => {
    if (message) {
      setMessages((prevMessages) => [
        ...prevMessages,
        {
          message: message.message,
          sentTime: new Date().toISOString(),
          sender: Role.User,
        },
      ]);
    }

    const websocket = connectWebSocket();
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

      assignOnMessageHanlder(websocket);

      websocket.send(
        JSON.stringify({
          input: message.message,
        })
      );
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

  return (
    <div className="flex flex-col h-[calc(100vh-4.6rem)]">
      <div className="flex-1 overflow-hidden">
        <ChatContainer messages={messages} onSendMessage={onSendMessage} />
      </div>
    </div>
  );
}
