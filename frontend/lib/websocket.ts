import { returnWebSockerURL } from "@/lib/utils";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";


export const connectWebSocket = async () => {
  let websocket: WebSocket;
  try {
    const session = await getServerSession(authOptions);
    const wsUrl = returnWebSockerURL(session, "generate_schedule");
    websocket = new WebSocket(wsUrl.toString());

    websocket.onerror = (error) => {
      console.error("WebSocket error:", error);
      // toast({
      //   title: "Connection Error",
      //   description: "WebSocket connection failed",
      //   variant: "destructive",
      //   duration: 4000,
      // });
    };
  } catch (error) {
    console.error("Failed to connect to WebSocket:", error);
    // toast({
    //   title: "Error",
    //   description: "Failed to connect to WebSocket",
    //   variant: "destructive",
    //   duration: 4000,
    // });
    return;
  }
  return websocket;
};

