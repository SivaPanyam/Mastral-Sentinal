type EventCallback = (payload: any) => void;

class WebSocketService {
  private socket: WebSocket | null = null;
  private listeners: Record<string, EventCallback[]> = {};
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connect() {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    
    // Default to localhost:8000 for local development if not in production
    const wsUrl = process.env.NODE_ENV === 'production' 
      ? `wss://${window.location.host}/api/v1/ws/events`
      : `ws://localhost:8000/api/v1/ws/events`;
    
    this.socket = new WebSocket(wsUrl);

    this.socket.onopen = () => {
      console.log('Global WebSocket connected for real-time events.');
      this.reconnectAttempts = 0;
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data && data.type) {
          const callbacks = this.listeners[data.type] || [];
          callbacks.forEach(cb => cb(data.payload));
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    this.socket.onclose = () => {
      console.log('Global WebSocket disconnected.');
      this.attemptReconnect();
    };

    this.socket.onerror = (err) => {
      console.error('WebSocket encountered an error:', err);
      this.socket?.close();
    };
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const timeout = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);
      console.log(`Reconnecting in ${timeout / 1000} seconds...`);
      setTimeout(() => this.connect(), timeout);
    } else {
      console.error('Max WebSocket reconnect attempts reached.');
    }
  }

  subscribe(eventType: string, callback: EventCallback) {
    if (!this.listeners[eventType]) {
      this.listeners[eventType] = [];
    }
    this.listeners[eventType].push(callback);
    return () => this.unsubscribe(eventType, callback); // Returns an unsubscribe function
  }

  unsubscribe(eventType: string, callback: EventCallback) {
    if (!this.listeners[eventType]) return;
    this.listeners[eventType] = this.listeners[eventType].filter(cb => cb !== callback);
  }
}

export const wsService = new WebSocketService();
