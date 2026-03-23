import './app.css';
import App from './App.svelte';
import { mount } from "svelte";
import { StatusBar, Style } from '@capacitor/status-bar';
import { EdgeToEdge } from '@capawesome/capacitor-android-edge-to-edge-support';
import { App as CapApp } from '@capacitor/app';
import { Capacitor } from '@capacitor/core';

// Initialize Android edge-to-edge support and status bar
async function initializeEdgeToEdgeAndStatusBar() {
  const storedTheme = localStorage.getItem('nmkorps-theme');
  const prefersDark = window.matchMedia?.('(prefers-color-scheme: dark)').matches;
  const isDarkMode = storedTheme === 'dark' || (!storedTheme && prefersDark);
  const bgColor = isDarkMode ? '#0f172a' : '#f8fafc';
  
  try {
    // Enable edge-to-edge on Android and set background color
    await EdgeToEdge.enable();
    await EdgeToEdge.setBackgroundColor({ color: bgColor });
    console.log('Edge-to-edge display enabled with background:', bgColor);
  } catch (err) {
    // Plugin not available (iOS/web)
    console.log('Edge-to-edge plugin skipped:', err);
  }
  
  try {
    // Set status bar style for iOS/Android
    if (isDarkMode) {
      await StatusBar.setStyle({ style: Style.Dark }); // Light text for dark mode
      await StatusBar.setBackgroundColor({ color: bgColor });
    } else {
      await StatusBar.setStyle({ style: Style.Light }); // Dark text for light mode
      await StatusBar.setBackgroundColor({ color: bgColor });
    }
  } catch (err) {
    // Status bar plugin not available (web/browser)
    console.log('Status Bar initialization skipped:', err);
  }
}

// Handle Android back button / swipe-back gesture (fallback for older Android)
if (Capacitor.isNativePlatform()) {
  CapApp.addListener('backButton', ({ canGoBack }) => {
    if (canGoBack) {
      window.history.back();
    } else {
      CapApp.exitApp();
    }
  });
}

// Initialize edge-to-edge and status bar, then mount app
initializeEdgeToEdgeAndStatusBar().then(() => {
  const app = mount(App, {
    target: document.getElementById('app') as HTMLElement
  });
  
  (window as any).app = app;
}).catch(err => {
  console.error('Status bar initialization failed:', err);
  // Mount app anyway
  const app = mount(App, {
    target: document.getElementById('app') as HTMLElement
  });
  
  (window as any).app = app;
});
