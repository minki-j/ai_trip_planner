"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import { redirect } from "next/navigation";

import ChatContainer from "../components/ChatContainer";

import { Message } from "@/types/types";

export default function Home() {
  const { data: session, status } = useSession();
  const [messages, setMessages] = useState<Message[]>([]);

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


  const handleSendMessage = async (message: Message) => {
    if (message) {
      setMessages((prevMessages) => [
        ...prevMessages,
        {
          message: message.message,
          sentTime: new Date().toISOString(),
          sender: "User",
        },
      ]);
    }

    try {
      const response = await fetch("/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: message,
        }),
      });

      const data = await response.json();
      console.log(data);

      setMessages((prevMessages) => [
        ...prevMessages,
        {
          message: data.message_from_interviewer,
          sentTime: new Date().toISOString(),
          sender: "Assistant",
        },
      ]);
    } catch (error) {}
  };

  return (
    <div className="max-w-4xl mx-auto h-full">
      <ChatContainer
        messages={messages}
        setMessages={setMessages}
        onSendMessage={handleSendMessage}
      />
    </div>
  );
}
