import { returnWebSockerURL } from "@/lib/utils";

const connectWebSocket = () => {
  let websocket: WebSocket;
  try {
    const wsUrl = returnWebSockerURL(null, "generate_schedule");
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

const assignOnMessageHanlder = async (websocket: WebSocket) => {
  websocket.onmessage = async (event) => {
    const response = JSON.parse(event.data);
    console.log("WebSocket response: ", response);
    if (!response) return;
    if (response.error) {
      console.error("Error:", response.error);
    //   toast({
    //     title: "Error",
    //     description: response.error,
    //     variant: "destructive",
    //     duration: 4000,
    //   });
      return;
    }

    // setMessages((prevMessages) => [
    //   ...prevMessages,
    //   {
    //     message: response.message,
    //     sender: response.role,
    //     sentTime: new Date().toISOString(),
    //   },
    // ]);
  };
};

export const onSendMessage = async (message: Message) => {
//   if (message) {
//     setMessages((prevMessages) => [
//       ...prevMessages,
//       {
//         message: message.message,
//         sentTime: new Date().toISOString(),
//         sender: Role.User,
//       },
//     ]);
//   }

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
    // toast({
    //   title: "Error",
    //   description: `${
    //     error.message ? error.message : "Sorry something went wrong"
    //   }`,
    //   variant: "destructive",
    //   duration: 4000,
    // });
  }
};
