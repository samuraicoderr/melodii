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
