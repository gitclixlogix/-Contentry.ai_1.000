import React from 'react';
import ReactDOM from 'react-dom/client';
import { OutlookAddin } from './OutlookAddin';
import './styles.css';

declare const Office: any;

// Wait for Office.js to initialize
Office.onReady((info: { host: string; platform: string }) => {
  console.log(`Office.js ready. Host: ${info.host}, Platform: ${info.platform}`);
  
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <OutlookAddin />
    </React.StrictMode>
  );
});
