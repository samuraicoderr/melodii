import { apiClient } from "../ApiClient";
import { BackendRoutes } from "../BackendRoutes";
import type { GenreClassificationJobResponse } from "../types";

export class GenreAIService {
  static async classify(file: File, modelName: string): Promise<GenreClassificationJobResponse> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("model_name", modelName);

    const res = await apiClient.post<GenreClassificationJobResponse>(
      BackendRoutes.genreAi.classify,
      formData,
      {
        requiresAuth: false,
      }
    );

    return res.data;
  }
}

export default GenreAIService;
