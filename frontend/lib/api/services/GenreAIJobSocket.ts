import type { GenreAIWebSocketEvent } from "../types";

type GenreAIJobSocketHandlers = {
  onEvent: (event: GenreAIWebSocketEvent) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (message: string) => void;
};

export class GenreAIJobSocket {
  private socket: WebSocket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private closedByClient = false;
  private terminalEventReceived = false;
  private reconnectAttempts = 0;

  constructor(
    private readonly url: string,
    private readonly handlers: GenreAIJobSocketHandlers,
    private readonly maxReconnectAttempts = 8,
  ) {}

  connect(): void {
    this.closedByClient = false;
    this.openSocket();
  }

  close(): void {
    this.closedByClient = true;
    this.clearTimers();
    this.socket?.close(1000, "Client closed");
    this.socket = null;
  }

  private openSocket(): void {
    this.clearReconnectTimer();
    this.socket = new WebSocket(this.url);

    this.socket.onopen = () => {
      this.reconnectAttempts = 0;
      this.handlers.onOpen?.();
      this.startHeartbeat();
    };

    this.socket.onmessage = (event) => {
      const message = this.parseEvent(event.data);
      if (!message) {
        return;
      }

      if (message.type === "result" || message.type === "error" || message.type === "done") {
        this.terminalEventReceived = message.type !== "done" || this.terminalEventReceived;
      }

      this.handlers.onEvent(message);
    };

    this.socket.onerror = () => {
      this.handlers.onError?.("Live log connection hit a network issue.");
    };

    this.socket.onclose = () => {
      this.stopHeartbeat();
      this.handlers.onClose?.();
      if (!this.closedByClient && !this.terminalEventReceived) {
        this.scheduleReconnect();
      }
    };
  }

  private parseEvent(data: string): GenreAIWebSocketEvent | null {
    try {
      return JSON.parse(data) as GenreAIWebSocketEvent;
    } catch {
      this.handlers.onError?.("Received an unreadable live log message.");
      return null;
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.handlers.onError?.("Live log connection closed before the task finished.");
      return;
    }

    this.reconnectAttempts += 1;
    const delay = Math.min(1000 * 1.5 ** (this.reconnectAttempts - 1), 10000);
    this.reconnectTimer = setTimeout(() => this.openSocket(), delay);
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      if (this.socket?.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({ type: "ping" }));
      }
    }, 25000);
  }

  private clearTimers(): void {
    this.clearReconnectTimer();
    this.stopHeartbeat();
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }
}
