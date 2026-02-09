import { STORAGE_KEYS } from '~/lib/config';

export {};

// Handle extension icon click - open side panel
chrome.action.onClicked.addListener(async (tab) => {
  if (tab.windowId) {
    try {
      await chrome.sidePanel.open({ windowId: tab.windowId });
    } catch (error) {
      console.error('Failed to open side panel:', error);
    }
  }
});

// Set side panel behavior
chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(console.error);

// Listen for messages
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Forward content updates to side panel
  if (message.type === 'CONTENT_UPDATED') {
    // Broadcast to all extension pages (side panel will receive this)
    chrome.runtime.sendMessage(message).catch(() => {
      // Side panel might not be open
    });
  }
  
  // Handle auth callback
  if (message.type === 'AUTH_SUCCESS') {
    const { user } = message.payload;
    chrome.storage.local.set({ [STORAGE_KEYS.USER_DATA]: user }).then(() => {
      // Notify all extension pages
      chrome.runtime.sendMessage({ type: 'AUTH_SUCCESS', payload: { user } }).catch(() => {});
    });
  }
  
  return true;
});

// Listen for tab URL changes to detect auth callback
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.url && changeInfo.url.includes('extension=true') && changeInfo.url.includes('auth_success=true')) {
    try {
      // Extract user data from URL parameters
      const url = new URL(changeInfo.url);
      const userData = url.searchParams.get('user_data');
      
      if (userData) {
        const user = JSON.parse(decodeURIComponent(userData));
        await chrome.storage.local.set({ [STORAGE_KEYS.USER_DATA]: user });
        
        // Close the auth tab
        chrome.tabs.remove(tabId);
        
        // Open side panel in the previous window
        const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (activeTab?.windowId) {
          chrome.sidePanel.open({ windowId: activeTab.windowId }).catch(console.error);
        }
      }
    } catch (error) {
      console.error('Error processing auth callback:', error);
    }
  }
});

console.log('[Contentry.ai] Background service worker initialized');
