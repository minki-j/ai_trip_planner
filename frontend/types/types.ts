export interface Message {
    message: string;
    sentTime?: string;
    sender: 'User' | 'Assistant' | 'display_decision';
}