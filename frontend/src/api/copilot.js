import apiClient from './client';

export const copilotApi = {
  /**
   * Send a natural-language shopping inquiry to the AI Shopping Copilot endpoint.
   * @param {string} message - Natural language shopping inquiry.
   * @returns {Promise<Object>} CopilotResponse payload.
   */
  async query(message) {
    return apiClient('/api/copilot', {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  },
};

export default copilotApi;
