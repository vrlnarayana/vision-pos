import { apiClient } from './client';
import { Session, SessionItemsResponse, CheckoutResponse } from '@/types';

interface DetectionResult {
  inventory_id: string;
  name: string;
  sku: string;
  confidence: number;
  quantity: number;
  matched_from: string;
}

interface ImageDetectionResponse {
  results: DetectionResult[];
  processing_time_ms: number;
  model_used: string;
}

export const sessionsApi = {
  checkout: (sessionId: string) =>
    apiClient.post<CheckoutResponse>(`/checkout/${sessionId}`, {}),

  detectFromImage: (sessionId: string, imageBase64: string) =>
    apiClient.post<ImageDetectionResponse>(
      `/sessions/${sessionId}/scan/detect-from-image`,
      { image_base64: imageBase64 }
    ),

  endSession: (sessionId: string) =>
    apiClient.post<Session>(`/sessions/${sessionId}/end`, {}),

  getSession: (sessionId: string) =>
    apiClient.get<Session>(`/sessions/${sessionId}`),

  getSessionItems: (sessionId: string) =>
    apiClient.get<SessionItemsResponse>(`/sessions/${sessionId}/items`),

  scanProduct: (sessionId: string, detectedName: string, confidence: number) =>
    apiClient.post(`/sessions/${sessionId}/scan`, {
      detected_name: detectedName,
      confidence,
    }),

  startSession: () => apiClient.post<Session>('/sessions/start', {}),
};
