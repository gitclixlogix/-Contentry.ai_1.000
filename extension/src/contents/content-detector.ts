import type { PlasmoCSConfig } from 'plasmo';

export const config: PlasmoCSConfig = {
  matches: ['<all_urls>'],
  all_frames: false,
};

// Debounce helper
function debounce<T extends (...args: any[]) => void>(fn: T, delay: number): T {
  let timeoutId: ReturnType<typeof setTimeout>;
  return ((...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  }) as T;
}

// Track the currently focused element
let currentFocusedElement: HTMLElement | null = null;
let lastContent = '';

// Get text content from an element
function getElementContent(element: HTMLElement): string {
  if (element instanceof HTMLTextAreaElement || element instanceof HTMLInputElement) {
    return element.value;
  }
  
  // For contenteditable elements
  if (element.isContentEditable) {
    return element.innerText || element.textContent || '';
  }
  
  return '';
}

// Check if element is a text input we should monitor
function isTextInputElement(element: Element | null): element is HTMLElement {
  if (!element) return false;
  
  // Check for textarea
  if (element instanceof HTMLTextAreaElement) return true;
  
  // Check for text input
  if (element instanceof HTMLInputElement) {
    const textTypes = ['text', 'email', 'search', 'url'];
    return textTypes.includes(element.type);
  }
  
  // Check for contenteditable
  if (element instanceof HTMLElement && element.isContentEditable) {
    return true;
  }
  
  return false;
}

// Determine field type
function getFieldType(element: HTMLElement): 'textarea' | 'contenteditable' | 'input' {
  if (element instanceof HTMLTextAreaElement) return 'textarea';
  if (element.isContentEditable) return 'contenteditable';
  return 'input';
}

// Send content update to side panel
const sendContentUpdate = debounce((content: string, fieldType: 'textarea' | 'contenteditable' | 'input') => {
  if (content === lastContent) return;
  lastContent = content;
  
  chrome.runtime.sendMessage({
    type: 'CONTENT_UPDATED',
    payload: {
      content,
      url: window.location.href,
      fieldType,
    },
  }).catch(() => {
    // Side panel might not be open, ignore error
  });
}, 500);

// Handle input events
function handleInput(event: Event) {
  const target = event.target as HTMLElement;
  if (!isTextInputElement(target)) return;
  
  const content = getElementContent(target);
  const fieldType = getFieldType(target);
  sendContentUpdate(content, fieldType);
}

// Handle focus events
function handleFocus(event: FocusEvent) {
  const target = event.target as HTMLElement;
  if (!isTextInputElement(target)) return;
  
  currentFocusedElement = target;
  const content = getElementContent(target);
  const fieldType = getFieldType(target);
  
  // Send initial content when focusing
  sendContentUpdate(content, fieldType);
}

// Handle blur events
function handleBlur(event: FocusEvent) {
  const target = event.target as HTMLElement;
  if (target === currentFocusedElement) {
    currentFocusedElement = null;
  }
}

// Listen for messages from side panel
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'GET_ACTIVE_CONTENT') {
    // Find active text field and send its content
    const activeElement = document.activeElement;
    
    if (isTextInputElement(activeElement)) {
      const content = getElementContent(activeElement);
      const fieldType = getFieldType(activeElement);
      
      chrome.runtime.sendMessage({
        type: 'CONTENT_UPDATED',
        payload: {
          content,
          url: window.location.href,
          fieldType,
        },
      }).catch(() => {});
    } else if (currentFocusedElement && isTextInputElement(currentFocusedElement)) {
      const content = getElementContent(currentFocusedElement);
      const fieldType = getFieldType(currentFocusedElement);
      
      chrome.runtime.sendMessage({
        type: 'CONTENT_UPDATED',
        payload: {
          content,
          url: window.location.href,
          fieldType,
        },
      }).catch(() => {});
    }
    
    sendResponse({ received: true });
  }
  
  return true;
});

// Set up event listeners
document.addEventListener('input', handleInput, true);
document.addEventListener('focus', handleFocus, true);
document.addEventListener('blur', handleBlur, true);

// Also watch for changes in contenteditable using MutationObserver
const observer = new MutationObserver((mutations) => {
  for (const mutation of mutations) {
    if (mutation.type === 'characterData' || mutation.type === 'childList') {
      const target = mutation.target;
      const editableParent = target instanceof Element 
        ? target.closest('[contenteditable="true"]')
        : target.parentElement?.closest('[contenteditable="true"]');
        
      if (editableParent && isTextInputElement(editableParent)) {
        const content = getElementContent(editableParent);
        sendContentUpdate(content, 'contenteditable');
      }
    }
  }
});

observer.observe(document.body, {
  characterData: true,
  childList: true,
  subtree: true,
});

console.log('[Contentry.ai] Content detector initialized');
