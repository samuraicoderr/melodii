export interface GenrePrediction {
  label: string;
  score: number;
}

export interface GenreClassificationResponse {
  success: boolean;
  model_used: string;
  filename: string;
  top_prediction: GenrePrediction;
  predictions: GenrePrediction[];
}

export interface GenreClassificationJobResponse {
  success: boolean;
  task_id: string;
  status: "queued";
  websocket_url: string;
}

export interface GenreAILogEvent {
  type: "log";
  task_id: string;
  timestamp: string;
  level: "info" | "warning" | "error" | string;
  message: string;
}

export interface GenreAIResultEvent {
  type: "result";
  task_id: string;
  timestamp: string;
  payload: GenreClassificationResponse;
}

export interface GenreAIErrorEvent {
  type: "error";
  task_id?: string;
  timestamp?: string;
  message: string;
}

export interface GenreAIDoneEvent {
  type: "done";
  task_id: string;
  timestamp: string;
  status: "completed" | "failed";
}

export type GenreAIWebSocketEvent =
  | GenreAILogEvent
  | GenreAIResultEvent
  | GenreAIErrorEvent
  | GenreAIDoneEvent
  | { type: "pong" };
