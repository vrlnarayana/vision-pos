import { useEffect, useState } from 'react';
import { ScanProductForm } from '@/components/ScanProductForm';
import { ScannedItemsList } from '@/components/ScannedItemsList';
import { WebcamScanner } from '@/components/WebcamScanner';
import { sessionsApi } from '@/api/sessions';
import { useApi } from '@/hooks/useApi';
import { SessionItemsResponse } from '@/types';

export function ScanSessionPage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionItems, setSessionItems] = useState<SessionItemsResponse | null>(
    null
  );
  const [error, setError] = useState<string | null>(null);
  const [scanMethod, setScanMethod] = useState<'manual' | 'webcam'>('manual');

  const startSessionApi = useApi(sessionsApi.startSession);
  const scanProductApi = useApi(sessionsApi.scanProduct);
  const getSessionItemsApi = useApi(sessionsApi.getSessionItems);
  const checkoutApi = useApi(sessionsApi.checkout);

  useEffect(() => {
    initializeSession();
  }, []);

  const initializeSession = async () => {
    try {
      setError(null);
      const session = await startSessionApi.execute();
      setSessionId(session.id);
      await loadSessionItems(session.id);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to start session';
      setError(message);
    }
  };

  const loadSessionItems = async (id: string) => {
    try {
      const items = await getSessionItemsApi.execute(id);
      setSessionItems(items);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to load items';
      setError(message);
    }
  };

  const handleScanProduct = async (
    detectedName: string,
    confidence: number
  ) => {
    if (!sessionId) {
      setError('No active session');
      return;
    }

    try {
      setError(null);
      await scanProductApi.execute(sessionId, detectedName, confidence);
      await loadSessionItems(sessionId);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to scan product';
      setError(message);
    }
  };

  const handleWebcamDetection = async (detectedProducts: any[]) => {
    if (!sessionId) {
      setError('No active session');
      return;
    }

    try {
      setError(null);
      for (const product of detectedProducts) {
        await scanProductApi.execute(
          sessionId,
          product.name,
          product.confidence
        );
      }
      await loadSessionItems(sessionId);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to process webcam detection';
      setError(message);
    }
  };

  const handleCheckout = async () => {
    if (!sessionId) {
      setError('No active session');
      return;
    }

    try {
      setError(null);
      await checkoutApi.execute(sessionId);
      setSessionItems(null);
      await initializeSession();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to checkout';
      setError(message);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">Scan Session</h1>
          {sessionId && (
            <div className="text-sm text-gray-600">
              Session ID: <span className="font-mono">{sessionId}</span>
            </div>
          )}
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="mb-4 flex gap-2 border-b">
                <button
                  onClick={() => setScanMethod('manual')}
                  className={`px-4 py-2 font-medium border-b-2 ${
                    scanMethod === 'manual'
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Manual Entry
                </button>
                <button
                  onClick={() => setScanMethod('webcam')}
                  className={`px-4 py-2 font-medium border-b-2 ${
                    scanMethod === 'webcam'
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Webcam Scanner
                </button>
              </div>

              {scanMethod === 'manual' ? (
                <div>
                  <h2 className="text-lg font-semibold mb-4">Scan Product</h2>
                  <ScanProductForm
                    onSubmit={handleScanProduct}
                    loading={scanProductApi.loading}
                  />
                </div>
              ) : (
                <div>
                  <h2 className="text-lg font-semibold mb-4">Webcam Scanner</h2>
                  {sessionId && (
                    <WebcamScanner
                      sessionId={sessionId}
                      onProductsDetected={handleWebcamDetection}
                      disabled={scanProductApi.loading}
                    />
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="lg:col-span-2">
            <div className="bg-white p-6 rounded-lg shadow">
              {sessionItems ? (
                <>
                  <ScannedItemsList
                    items={sessionItems.items}
                    subtotal={sessionItems.subtotal}
                  />
                  <div className="mt-6 flex gap-4">
                    <button
                      onClick={handleCheckout}
                      disabled={
                        checkoutApi.loading ||
                        sessionItems.items.length === 0
                      }
                      className="flex-1 bg-green-600 text-white py-2 rounded font-medium hover:bg-green-700 disabled:bg-gray-400"
                    >
                      {checkoutApi.loading ? 'Processing...' : 'Checkout'}
                    </button>
                    <button
                      onClick={initializeSession}
                      disabled={
                        startSessionApi.loading || checkoutApi.loading
                      }
                      className="flex-1 bg-gray-600 text-white py-2 rounded font-medium hover:bg-gray-700 disabled:bg-gray-400"
                    >
                      New Session
                    </button>
                  </div>
                </>
              ) : (
                <p className="text-gray-500">Loading session...</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
