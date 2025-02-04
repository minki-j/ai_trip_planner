import { useRef, useState, useEffect, useContext } from "react";
import { useParams } from "react-router-dom";
import "@chatscope/chat-ui-kit-styles/dist/default/styles.min.css";
import {
  MainContainer,
  ChatContainer as ChatUI,
  MessageList,
  MessageInput,
} from "@chatscope/chat-ui-kit-react";
import ChatMessage from "./ChatMessage";
import { Message } from "@/types/types";

interface ChatContainerProps {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  onSendMessage: (message: Message) => void;
}


const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  setMessages,
  onSendMessage,
}) => {
  const [inputValue, setInputValue] = useState<string>("");
  const [recordingDisabled, setRecordingDisabled] = useState<boolean>(false);
  const { id } = useParams();
  const messageListRef = useRef<HTMLDivElement>(null);

  const fullTranscriptRef = useRef<string>("");

  if (!("webkitSpeechRecognition" in window)) {
    console.log("Speech recognition is not supported in this browser");
    setRecordingDisabled(true);
  }

  const stripHtmlTags = (html: string): string => {
    const tmp = document.createElement("div");
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || "";
  };

  const handleResponse = async (accepted: boolean): Promise<void> => {
    
  };

  const handlePaste = (e: React.ClipboardEvent): void => {
    e.preventDefault();
    const text = e.clipboardData.getData("text/plain");
    setInputValue(text);
  };

  return (
    <MainContainer className="flex flex-col h-full">
      <ChatUI className="flex flex-col flex-1 min-h-0">
        <MessageList ref={messageListRef} className="flex-1 overflow-y-auto">
          {messages.map((msg, index) => (
            <ChatMessage key={index} role={msg.sender} content={msg.message} />
          ))}
        </MessageList>
        <MessageInput
          value={inputValue}
          onChange={(val) => {
            setInputValue(val);
            fullTranscriptRef.current = val;
          }}
          placeholder="Type message here"
          onPaste={handlePaste}
          onSend={(val) => {
            const cleanMessage = stripHtmlTags(val);
            onSendMessage(cleanMessage);
            setInputValue("");
            fullTranscriptRef.current = "";
          }}
          sendButton={true}
          sendDisabled={false}
          attachButton={!recordingDisabled}
        />
      </ChatUI>
    </MainContainer>
  );
};

export default ChatContainer;
