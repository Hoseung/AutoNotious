export interface SSEOptions {
  onMessage: (data: string) => void;
  onError?: (error: Error) => void;
  onEnd?: () => void;
}

export class SSEClient {
  private eventSource: EventSource | null = null;
  private controller: AbortController | null = null;

  async connect(
    sessionId: string,
    text: string,
    options: SSEOptions
  ): Promise<void> {
    const API_BASE_URL = 'http://localhost:8000/api';
    
    this.controller = new AbortController();
    
    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ session_id: sessionId, text }),
        signal: this.controller.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          options.onEnd?.();
          break;
        }

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            try {
              const parsed = JSON.parse(data);
              
              if (parsed.error) {
                options.onError?.(new Error(parsed.error));
              } else if (parsed.event === 'end') {
                options.onEnd?.();
              } else if (parsed.data) {
                options.onMessage(parsed.data);
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    } catch (error) {
      if (error instanceof Error && error.name !== 'AbortError') {
        options.onError?.(error);
      }
    }
  }

  disconnect(): void {
    if (this.controller) {
      this.controller.abort();
      this.controller = null;
    }
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}