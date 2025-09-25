import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

// API functions for calculations
export const calculationsAPI = {
  // Get all calculations
  getCalculations: async () => {
    try {
      const response = await axios.get(`${API_BASE}/calculations/`);
      return response.data;
    } catch (error) {
      console.error('Error fetching calculations:', error);
      throw new Error('Erreur lors de la récupération des calculs');
    }
  },

  // Save a new calculation
  saveCalculation: async (calculationData) => {
    try {
      const response = await axios.post(`${API_BASE}/calculations/`, calculationData);
      return response.data;
    } catch (error) {
      console.error('Error saving calculation:', error);
      throw new Error('Erreur lors de la sauvegarde du calcul');
    }
  },

  // Delete a calculation
  deleteCalculation: async (calculationId) => {
    try {
      const response = await axios.delete(`${API_BASE}/calculations/${calculationId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting calculation:', error);
      throw new Error('Erreur lors de la suppression du calcul');
    }
  }
};