import { apiClient } from "../ApiClient";
import { BackendRoutes } from "../BackendRoutes";
import type { GenreClassificationResponse } from "../types";

export class GenreAIService {
  static async classify(file: File, modelName: string): Promise<GenreClassificationResponse> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("model_name", modelName);

    const res = await apiClient.post<GenreClassificationResponse>(
      BackendRoutes.genreAi.classify,
      formData,
      {
        requiresAuth: false,
        headers: {
          "Content-Type": undefined as any,
        },
      }
    );

    return res.data;
  }
}

export default GenreAIService;
