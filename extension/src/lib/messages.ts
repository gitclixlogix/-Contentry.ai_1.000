// Message types for communication between extension parts

export type MessageType =
  | 'CONTENT_UPDATED'
  | 'REQUEST_ANALYSIS'
  | 'ANALYSIS_RESULT'
  | 'AUTH_SUCCESS'
  | 'AUTH_LOGOUT'
  | 'OPEN_SIDEPANEL'
  | 'GET_ACTIVE_CONTENT';

export interface ExtensionMessage {
  type: MessageType;
  payload?: any;
}

export interface ContentUpdatePayload {
  content: string;
  url: string;
  fieldType: 'textarea' | 'contenteditable' | 'input';
}

export interface AnalysisResultPayload {
  success: boolean;
  result?: any;
  error?: string;
}

// Send message to background script
export async function sendToBackground(message: ExtensionMessage): Promise<any> {
  return chrome.runtime.sendMessage(message);
}

// Send message to content script in active tab
export async function sendToActiveTab(message: ExtensionMessage): Promise<any> {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab?.id) {
    return chrome.tabs.sendMessage(tab.id, message);
  }
  return null;
}
