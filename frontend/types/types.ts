export interface Message {
    message: string;
    sentTime?: string;
    sender: Role;
}

export enum Role {
  User = "User",
  Assistant = "Assistant",
  ReasoningStep = "ReasoningStep",
}