import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';
import jsPDF from 'jspdf';
import 'jspdf-autotable';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const VEHICLE_TYPES = {
  'CAMPING-CAR': 'CAMPING-CAR',
  'FOURGON': 'FOURGON',
  'VAN': 'VAN'
};

const Dashboard = ({ stats, config, onPeriodChange }) => {
  const [startDate, setStartDate] = useState('2025-09-01');
  const [endDate, setEndDate] = useState('2026-08-31');
  const [isExporting, setIsExporting] = useState(false);

  const handlePeriodChange = () => {
    onPeriodChange(startDate, endDate);
  };

  const handleExportPDF = async () => {
    setIsExporting(true);
    try {
      const response = await axios.post(`${API}/export-pdf?start_date=${startDate}&end_date=${endDate}`, {}, {
        responseType: 'blob'
      });
      
      // Create blob link to download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `salesboard_report_${startDate}_${endDate}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      alert('Rapport PDF exporté avec succès !');
    } catch (error) {
      console.error('Error exporting PDF:', error);
      alert('Erreur lors de l\'export PDF');
    } finally {
      setIsExporting(false);
    }
  };

  const getQ1Status = () => {
    const progress = stats.q1_prime_progress;
    const target = config.q1_prime_target;
    if (progress >= target) return { status: '🟢 Atteinte', color: 'text-green-600' };
    if (progress > target * 0.7) return { status: '🟡 En cours', color: 'text-yellow-600' };
    return { status: '🔴 Non atteinte', color: 'text-red-600' };
  };

  const getCAPrimeLevel = () => {
    const vehicles = stats.ca_prime_progress; // Now it's the number of vehicles
    const thresholds = config.ca_prime_thresholds;
    
    if (vehicles >= 90) return { level: 90, prime: thresholds['90'], color: 'bg-green-500' };
    if (vehicles >= 70) return { level: 70, prime: thresholds['70'], color: 'bg-green-500' };
    if (vehicles >= 60) return { level: 60, prime: thresholds['60'], color: 'bg-green-500' };
    if (vehicles >= 50) return { level: 50, prime: thresholds['50'], color: 'bg-green-500' };
    return { level: 0, prime: 0, color: 'bg-red-500' };
  };

  const q1Status = getQ1Status();
  const caPrime = getCAPrimeLevel();

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">📊 SALESBOARD TPL - Tableau de Bord</h1>
        
        {/* Period Selector */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">📅 Période d'analyse</h2>
          <div className="flex flex-wrap gap-4 items-center">
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="border rounded px-3 py-2"
            />
            <span>à</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="border rounded px-3 py-2"
            />
            <button
              onClick={handlePeriodChange}
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              Actualiser
            </button>
            <button
              onClick={handleExportPDF}
              disabled={isExporting}
              className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 disabled:bg-gray-400"
            >
              {isExporting ? 'Export en cours...' : '📄 Export PDF'}
            </button>
          </div>
        </div>

        {/* Dynamic Bubbles */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <div className="text-3xl font-bold text-blue-600">{stats.vn_livres}</div>
            <div className="text-sm text-gray-600">VN Livrés</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <div className="text-3xl font-bold text-green-600">{stats.vo_livres}</div>
            <div className="text-sm text-gray-600">VO Livrés</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <div className="text-3xl font-bold text-red-600">{stats.ventes_annulees}</div>
            <div className="text-sm text-gray-600">Ventes Annulées</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <div className="text-3xl font-bold text-orange-600">{stats.taux_annulation}%</div>
            <div className="text-sm text-gray-600">Taux d'Annulation</div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <div className="text-2xl font-bold text-purple-600">{stats.ca_cumule.toLocaleString()}€</div>
            <div className="text-sm text-gray-600">CA Cumulé</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <div className="text-2xl font-bold text-indigo-600">{stats.ca_mensuel.toLocaleString()}€</div>
            <div className="text-sm text-gray-600">CA Mensuel</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <div className="text-2xl font-bold text-teal-600">{stats.vehicules_livres_ce_mois}</div>
            <div className="text-sm text-gray-600">Véhicules ce mois</div>
          </div>
        </div>

        {/* Q1 Prime Gauge */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">🎯 PRIME Q1 - Ventes VN + VO</h2>
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm text-gray-600">0</span>
            <span className={`font-semibold ${q1Status.color}`}>{q1Status.status}</span>
            <span className="text-sm text-gray-600">35</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-8">
            <div 
              className={`h-8 rounded-full transition-all duration-300 ${
                stats.q1_prime_progress >= config.q1_prime_target ? 'bg-green-500' : 'bg-blue-500'
              }`}
              style={{ width: `${Math.min((stats.q1_prime_progress / config.q1_prime_target) * 100, 100)}%` }}
            ></div>
          </div>
          <div className="text-center mt-2">
            <span className="text-lg font-semibold">{stats.q1_prime_progress} / {config.q1_prime_target}</span>
            {stats.q1_prime_progress >= config.q1_prime_target && (
              <span className="ml-2 text-green-600 font-semibold">Prime: {config.q1_prime_amount}€</span>
            )}
          </div>
        </div>

        {/* CA Prime Gauge */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">💰 PRIME SUR VENTE - Nombre de Véhicules</h2>
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm text-gray-600">0 véhicules</span>
            <span className="font-semibold">Prime: {caPrime.prime}€</span>
            <span className="text-sm text-gray-600">90 véhicules</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-8">
            <div 
              className={`h-8 rounded-full transition-all duration-300 ${caPrime.color}`}
              style={{ width: `${Math.min((stats.ca_prime_progress / 90) * 100, 100)}%` }}
            ></div>
          </div>
          <div className="text-center mt-2">
            <span className="text-lg font-semibold">{stats.ca_prime_progress} / 90 véhicules</span>
          </div>
          <div className="mt-4 text-sm text-gray-600">
            <div className="flex justify-between">
              <span className={stats.ca_prime_progress >= 50 ? 'text-green-600 font-semibold' : ''}>
                50 véhicules → 5,000€
              </span>
              <span className={stats.ca_prime_progress >= 60 ? 'text-green-600 font-semibold' : ''}>
                60 véhicules → 6,000€
              </span>
              <span className={stats.ca_prime_progress >= 70 ? 'text-green-600 font-semibold' : ''}>
                70 véhicules → 7,000€
              </span>
              <span className={stats.ca_prime_progress >= 90 ? 'text-green-600 font-semibold' : ''}>
                90 véhicules → 11,000€
              </span>
            </div>
          </div>
        </div>

        {/* Commission Display */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">📈 Commission sur Vente</h2>
            <div className="text-3xl font-bold text-blue-600">{stats.commission_vente.toLocaleString()}€</div>
            <div className="text-sm text-gray-600 mt-2">Période sélectionnée</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">🏦 Commission sur Financement</h2>
            <div className="text-3xl font-bold text-green-600">{stats.commission_financement.toLocaleString()}€</div>
            <div className="text-sm text-gray-600 mt-2">Basé sur PC saisis</div>
          </div>
        </div>
      </div>
    </div>
  );
};

const CommissionSettings = ({ onSettingsChange }) => {
  const [rates, setRates] = useState({
    payplan_rates: {
      camping_car: 0.055,
      fourgon_van: 0.065
    },
    financing_rates: {
      "0": 0.005,
      "1": 0.060,
      "2": 0.065,
      "3": 0.075,
      "4": 0.080
    },
    q1_prime: {
      amount: 1500.0,
      target: 35
    },
    ca_prime_thresholds: {
      "50": 5000,
      "60": 6000,
      "70": 7000,
      "90": 11000
    }
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadRates();
  }, []);

  const loadRates = async () => {
    try {
      const response = await axios.get(`${API}/commission-rates`);
      setRates(response.data);
    } catch (error) {
      console.error('Error loading rates:', error);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    setMessage('');
    try {
      await axios.put(`${API}/commission-rates`, rates);
      setMessage('Configuration sauvegardée avec succès !');
      onSettingsChange();
    } catch (error) {
      console.error('Error saving rates:', error);
      setMessage('Erreur lors de la sauvegarde');
    } finally {
      setLoading(false);
    }
  };

  const updatePayplanRate = (type, value) => {
    setRates(prev => ({
      ...prev,
      payplan_rates: {
        ...prev.payplan_rates,
        [type]: parseFloat(value)
      }
    }));
  };

  const updateFinancingRate = (pc, value) => {
    setRates(prev => ({
      ...prev,
      financing_rates: {
        ...prev.financing_rates,
        [pc]: parseFloat(value)
      }
    }));
  };

  const updateQ1Prime = (field, value) => {
    setRates(prev => ({
      ...prev,
      q1_prime: {
        ...prev.q1_prime,
        [field]: field === 'amount' ? parseFloat(value) : parseInt(value)
      }
    }));
  };

  const updateCAPrimeThreshold = (threshold, value) => {
    setRates(prev => ({
      ...prev,
      ca_prime_thresholds: {
        ...prev.ca_prime_thresholds,
        [threshold]: parseInt(value)
      }
    }));
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">🛠️ Paramétrage des Commissions</h1>
        
        {message && (
          <div className={`mb-6 p-4 rounded-lg ${message.includes('succès') ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
            {message}
          </div>
        )}

        {/* PAYPLAN Rates */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">📑 PAYPLAN - Taux de Commission</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                CAMPING-CAR (%)
              </label>
              <input
                type="number"
                step="0.001"
                value={rates.payplan_rates.camping_car}
                onChange={(e) => updatePayplanRate('camping_car', e.target.value)}
                className="w-full border rounded px-3 py-2"
              />
              <p className="text-sm text-gray-500 mt-1">
                Actuel: {(rates.payplan_rates.camping_car * 100).toFixed(1)}%
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                FOURGON ou VAN (%)
              </label>
              <input
                type="number"
                step="0.001"
                value={rates.payplan_rates.fourgon_van}
                onChange={(e) => updatePayplanRate('fourgon_van', e.target.value)}
                className="w-full border rounded px-3 py-2"
              />
              <p className="text-sm text-gray-500 mt-1">
                Actuel: {(rates.payplan_rates.fourgon_van * 100).toFixed(1)}%
              </p>
            </div>
          </div>
        </div>

        {/* Financing Rates */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">📑 FINANCEMENT - Taux selon nombre de PC</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {Object.entries(rates.financing_rates).map(([pc, rate]) => (
              <div key={pc}>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {pc} PC
                </label>
                <input
                  type="number"
                  step="0.001"
                  value={rate}
                  onChange={(e) => updateFinancingRate(pc, e.target.value)}
                  className="w-full border rounded px-3 py-2"
                />
                <p className="text-sm text-gray-500 mt-1">
                  {(rate * 100).toFixed(1)}%
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Q1 Prime */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">🎯 PRIME Q1 - Configuration</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Montant de la Prime (€)
              </label>
              <input
                type="number"
                value={rates.q1_prime.amount}
                onChange={(e) => updateQ1Prime('amount', e.target.value)}
                className="w-full border rounded px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Objectif de ventes
              </label>
              <input
                type="number"
                value={rates.q1_prime.target}
                onChange={(e) => updateQ1Prime('target', e.target.value)}
                className="w-full border rounded px-3 py-2"
              />
            </div>
          </div>
        </div>

        {/* CA Prime Thresholds */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">💰 PRIME CA - Seuils par nombre de véhicules</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(rates.ca_prime_thresholds).map(([threshold, amount]) => (
              <div key={threshold}>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {threshold} véhicules → Prime (€)
                </label>
                <input
                  type="number"
                  value={amount}
                  onChange={(e) => updateCAPrimeThreshold(threshold, e.target.value)}
                  className="w-full border rounded px-3 py-2"
                />
              </div>
            ))}
          </div>
        </div>

        {/* Save Button */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <button
            onClick={handleSave}
            disabled={loading}
            className="w-full bg-blue-500 text-white py-3 px-6 rounded-lg hover:bg-blue-600 disabled:bg-gray-400 font-semibold"
          >
            {loading ? 'Sauvegarde en cours...' : '💾 Sauvegarder la Configuration'}
          </button>
        </div>
      </div>
    </div>
  );
};
  const [sales, setSales] = useState([]);
  const [formData, setFormData] = useState({
    nom: '',
    prenom: '',
    type: 'CAMPING-CAR',
    marque: '',
    modele: '',
    date_vente: '',
    date_livraison_previsionnelle: '',
    prix_vente: '',
    montant_financement: '',
    nombre_pc: 0,
    annulation: false
  });
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadSales();
  }, []);

  const loadSales = async () => {
    try {
      const response = await axios.get(`${API}/sales`);
      setSales(response.data);
      onSalesChange();
    } catch (error) {
      console.error('Error loading sales:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/sales`, {
        ...formData,
        prix_vente: parseFloat(formData.prix_vente),
        montant_financement: parseFloat(formData.montant_financement),
        nombre_pc: parseInt(formData.nombre_pc)
      });
      
      // Reset form
      setFormData({
        nom: '',
        prenom: '',
        type: 'CAMPING-CAR',
        marque: '',
        modele: '',
        date_vente: '',
        date_livraison_previsionnelle: '',
        prix_vente: '',
        montant_financement: '',
        nombre_pc: 0,
        annulation: false
      });
      
      loadSales();
    } catch (error) {
      console.error('Error creating sale:', error);
    }
  };

  const toggleCancellation = async (saleId, currentStatus) => {
    try {
      const sale = sales.find(s => s.id === saleId);
      await axios.put(`${API}/sales/${saleId}`, {
        ...sale,
        annulation: !currentStatus
      });
      loadSales();
    } catch (error) {
      console.error('Error updating sale:', error);
    }
  };

  const deleteSale = async (saleId) => {
    try {
      await axios.delete(`${API}/sales/${saleId}`);
      loadSales();
    } catch (error) {
      console.error('Error deleting sale:', error);
    }
  };

  const filteredSales = sales.filter(sale => {
    if (filter === 'all') return true;
    if (filter === 'cancelled') return sale.annulation;
    if (filter === 'active') return !sale.annulation;
    return sale.type === filter;
  });

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">📋 Suivi des Ventes</h1>
        
        {/* Sales Form */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Nouvelle Vente</h2>
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <input
              type="text"
              placeholder="Nom"
              value={formData.nom}
              onChange={(e) => setFormData({...formData, nom: e.target.value})}
              className="border rounded px-3 py-2"
              required
            />
            <input
              type="text"
              placeholder="Prénom"
              value={formData.prenom}
              onChange={(e) => setFormData({...formData, prenom: e.target.value})}
              className="border rounded px-3 py-2"
              required
            />
            <select
              value={formData.type}
              onChange={(e) => setFormData({...formData, type: e.target.value})}
              className="border rounded px-3 py-2"
            >
              {Object.entries(VEHICLE_TYPES).map(([key, value]) => (
                <option key={key} value={key}>{value}</option>
              ))}
            </select>
            <input
              type="text"
              placeholder="Marque"
              value={formData.marque}
              onChange={(e) => setFormData({...formData, marque: e.target.value})}
              className="border rounded px-3 py-2"
              required
            />
            <input
              type="text"
              placeholder="Modèle"
              value={formData.modele}
              onChange={(e) => setFormData({...formData, modele: e.target.value})}
              className="border rounded px-3 py-2"
              required
            />
            <input
              type="date"
              value={formData.date_vente}
              onChange={(e) => setFormData({...formData, date_vente: e.target.value})}
              className="border rounded px-3 py-2"
              required
            />
            <input
              type="date"
              value={formData.date_livraison_previsionnelle}
              onChange={(e) => setFormData({...formData, date_livraison_previsionnelle: e.target.value})}
              className="border rounded px-3 py-2"
              required
            />
            <input
              type="number"
              placeholder="Prix de vente"
              value={formData.prix_vente}
              onChange={(e) => setFormData({...formData, prix_vente: e.target.value})}
              className="border rounded px-3 py-2"
              required
            />
            <input
              type="number"
              placeholder="Montant financement"
              value={formData.montant_financement}
              onChange={(e) => setFormData({...formData, montant_financement: e.target.value})}
              className="border rounded px-3 py-2"
              required
            />
            <input
              type="number"
              placeholder="Nombre PC"
              value={formData.nombre_pc}
              onChange={(e) => setFormData({...formData, nombre_pc: e.target.value})}
              className="border rounded px-3 py-2"
              min="0"
              max="4"
              required
            />
            <button
              type="submit"
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 md:col-span-2 lg:col-span-1"
            >
              Ajouter Vente
            </button>
          </form>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Filtres</h2>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 rounded ${filter === 'all' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
            >
              Toutes ({sales.length})
            </button>
            <button
              onClick={() => setFilter('active')}
              className={`px-4 py-2 rounded ${filter === 'active' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
            >
              Actives ({sales.filter(s => !s.annulation).length})
            </button>
            <button
              onClick={() => setFilter('cancelled')}
              className={`px-4 py-2 rounded ${filter === 'cancelled' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
            >
              Annulées ({sales.filter(s => s.annulation).length})
            </button>
            {Object.entries(VEHICLE_TYPES).map(([key, value]) => (
              <button
                key={key}
                onClick={() => setFilter(key)}
                className={`px-4 py-2 rounded ${filter === key ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
              >
                {value} ({sales.filter(s => s.type === key).length})
              </button>
            ))}
          </div>
        </div>

        {/* Sales Table */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Client</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Véhicule</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date Vente</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Prix</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">PC</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Statut</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredSales.map((sale) => (
                  <tr key={sale.id} className={sale.annulation ? 'bg-red-50' : ''}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{sale.nom} {sale.prenom}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                        {sale.type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {sale.marque} {sale.modele}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {sale.date_vente}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {sale.prix_vente.toLocaleString()}€
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {sale.nombre_pc}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        sale.annulation ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                      }`}>
                        {sale.annulation ? 'Annulée' : 'Active'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => toggleCancellation(sale.id, sale.annulation)}
                        className={`mr-2 px-2 py-1 rounded text-xs ${
                          sale.annulation 
                            ? 'bg-green-500 text-white hover:bg-green-600' 
                            : 'bg-red-500 text-white hover:bg-red-600'
                        }`}
                      >
                        {sale.annulation ? 'Réactiver' : 'Annuler'}
                      </button>
                      <button
                        onClick={() => deleteSale(sale.id)}
                        className="px-2 py-1 bg-gray-500 text-white rounded text-xs hover:bg-gray-600"
                      >
                        Supprimer
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

const App = () => {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [stats, setStats] = useState({
    vn_livres: 0,
    vo_livres: 0,
    ventes_annulees: 0,
    taux_annulation: 0,
    ca_cumule: 0,
    ca_mensuel: 0,
    vehicules_livres_ce_mois: 0,
    q1_prime_progress: 0,
    ca_prime_progress: 0,
    commission_vente: 0,
    commission_financement: 0
  });
  const [config, setConfig] = useState({
    camping_car_rate: 0.055,
    fourgon_van_rate: 0.065,
    financing_rates: {
      "0": 0.005,
      "1": 0.060,
      "2": 0.065,
      "3": 0.075,
      "4": 0.080
    },
    q1_prime_amount: 1500.0,
    q1_prime_target: 35,
    ca_prime_thresholds: {
      "50": 5000,   // 50 véhicules → 5000€
      "60": 6000,   // 60 véhicules → 6000€
      "70": 7000,   // 70 véhicules → 7000€
      "90": 11000   // 90 véhicules → 11000€
    }
  });

  useEffect(() => {
    loadStats();
    loadConfig();
  }, []);

  const loadStats = async (startDate = '2025-09-01', endDate = '2026-08-31') => {
    try {
      const response = await axios.get(`${API}/stats?start_date=${startDate}&end_date=${endDate}`);
      setStats(response.data);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const loadConfig = async () => {
    try {
      const response = await axios.get(`${API}/config`);
      setConfig(response.data);
    } catch (error) {
      console.error('Error loading config:', error);
    }
  };

  const handlePeriodChange = (startDate, endDate) => {
    loadStats(startDate, endDate);
  };

  const handleSalesChange = () => {
    loadStats();
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex space-x-8">
              <button
                onClick={() => setCurrentPage('dashboard')}
                className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                  currentPage === 'dashboard'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                📊 Tableau de Bord
              </button>
              <button
                onClick={() => setCurrentPage('sales')}
                className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                  currentPage === 'sales'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                📋 Suivi des Ventes
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Page Content */}
      {currentPage === 'dashboard' && (
        <Dashboard 
          stats={stats} 
          config={config} 
          onPeriodChange={handlePeriodChange}
        />
      )}
      {currentPage === 'sales' && (
        <SalesTracking onSalesChange={handleSalesChange} />
      )}
    </div>
  );
};

export default App;