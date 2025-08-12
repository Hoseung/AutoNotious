import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Session {
  id: string;
  title: string | null;
  created_at: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface Summary {
  title: string;
  markdown: string;
}

export interface NotionPage {
  page_id: string;
  url: string;
}

export const sessionApi = {
  list: async (): Promise<{ sessions: Session[] }> => {
    const response = await api.get('/sessions');
    return response.data;
  },

  create: async (): Promise<{ id: string }> => {
    const response = await api.post('/sessions');
    return response.data;
  },

  get: async (sessionId: string): Promise<Session> => {
    const response = await api.get(`/sessions/${sessionId}`);
    return response.data;
  },

  getMessages: async (sessionId: string): Promise<{ messages: Message[] }> => {
    const response = await api.get(`/sessions/${sessionId}/messages`);
    return response.data;
  },

  summarize: async (sessionId: string): Promise<Summary> => {
    const response = await api.post(`/sessions/${sessionId}/summarize`);
    return response.data;
  },

  saveToNotion: async (sessionId: string): Promise<NotionPage> => {
    const response = await api.post(`/sessions/${sessionId}/notion`);
    return response.data;
  },

  delete: async (sessionId: string): Promise<{ message: string }> => {
    const response = await api.delete(`/sessions/${sessionId}`);
    return response.data;
  },
};

export const healthApi = {
  check: async (): Promise<{ ok: boolean }> => {
    const response = await api.get('/healthz');
    return response.data;
  },
};