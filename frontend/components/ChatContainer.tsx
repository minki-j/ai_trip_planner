import { useRef, useState } from "react";

import "@chatscope/chat-ui-kit-styles/dist/default/styles.min.css";
import {
  MainContainer,
  ChatContainer as ChatUI,
  MessageList,
  MessageInput,
} from "@chatscope/chat-ui-kit-react";

import ChatMessage from "./ChatMessage";
import { Message } from "@/types/types";

import {Role} from '@/types/types';

interface ChatContainerProps {
  messages: Message[];
  onSendMessage: (message: Message) => void;
}

const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  onSendMessage,
}) => {
  const [inputValue, setInputValue] = useState<string>("");

  const messageListRef = useRef<HTMLDivElement>(null);

  const fullTranscriptRef = useRef<string>("");

  const handlePaste = (e: React.ClipboardEvent): void => {
    e.preventDefault();
    const text = e.clipboardData.getData("text/plain");
    setInputValue(text);
  };

  const stripHtmlTags = (html: string): string => {
    const tmp = document.createElement("div");
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || "";
  };

  return (
    <MainContainer className="h-full">
      <ChatUI className="h-full">
        <MessageList ref={messageListRef} className="flex-1">
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
            onSendMessage({
              message: cleanMessage,
              sentTime: new Date().toISOString(),
              sender: Role.User,
            });
            setInputValue("");
            fullTranscriptRef.current = "";
          }}
          sendButton={true}
          sendDisabled={false}
          attachButton={false}
        />
      </ChatUI>
    </MainContainer>
  );
};

export default ChatContainer;
