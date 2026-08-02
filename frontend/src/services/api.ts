import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1',
});

export const datasetService = {
  upload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/datasets/upload', formData);
  },
  fetchDatasets: () => api.get('/datasets'),
  fetchSchema: (datasetId: string) => api.get(`/datasets/${datasetId}/schema`),
  askAnalyst: (datasetId: string, queryText: string) =>
    api.post(`/analyst/${datasetId}/query`, { query_text: queryText }),
};

export default api;
