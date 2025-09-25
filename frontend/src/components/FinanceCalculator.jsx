import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Button } from './ui/button';
import { Calculator, Euro, Users, Shield, FileText, Trash2, Loader2 } from 'lucide-react';
import { calculationsAPI } from '../api/calculations';
import { useToast } from '../hooks/use-toast';

const FinanceCalculator = () => {
  const [formData, setFormData] = useState({
    montantFinancer: '',
    coefficientEmprunteur: '',
    coefficientCoEmprunteur: '',
    coefficientComplementaire: '',
    extensionGarantie: '',
    revision: ''
  });

  const [calculations, setCalculations] = useState({
    mensualiteEmprunteur: 0,
    mensualiteCoEmprunteur: 0,
    complementaire: 0,
    mensualitesTotales: 0
  });

  const [savedCalculations, setSavedCalculations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const { toast } = useToast();

  // Load calculations from API on component mount
  useEffect(() => {
    loadCalculations();
  }, []);

  const loadCalculations = async () => {
    try {
      setLoading(true);
      const calculations = await calculationsAPI.getCalculations();
      setSavedCalculations(calculations);
    } catch (error) {
      toast({
        title: "Erreur",
        description: error.message,
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  // Recalculate when form data changes
  useEffect(() => {
    const montant = parseFloat(formData.montantFinancer) || 0;
    const coeffEmprunteur = (parseFloat(formData.coefficientEmprunteur) || 0) / 100;
    const coeffCoEmprunteur = (parseFloat(formData.coefficientCoEmprunteur) || 0) / 100;
    const coeffComplementaire = (parseFloat(formData.coefficientComplementaire) || 0) / 100;
    const extension = parseFloat(formData.extensionGarantie) || 0;
    const revision = parseFloat(formData.revision) || 0;

    const mensualiteEmprunteur = montant * coeffEmprunteur;
    const mensualiteCoEmprunteur = montant * coeffCoEmprunteur;
    const complementaire = montant * coeffComplementaire;
    const mensualitesTotales = mensualiteEmprunteur + mensualiteCoEmprunteur + complementaire + extension + revision;

    setCalculations({
      mensualiteEmprunteur,
      mensualiteCoEmprunteur,
      complementaire,
      mensualitesTotales
    });
  }, [formData]);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSaveCalculation = async () => {
    if (!formData.montantFinancer || calculations.mensualitesTotales === 0) {
      toast({
        title: "Erreur",
        description: "Veuillez remplir au moins le montant à financer",
        variant: "destructive"
      });
      return;
    }

    try {
      setSaving(true);
      const calculationData = {
        ...formData,
        ...calculations
      };

      await calculationsAPI.saveCalculation(calculationData);
      
      toast({
        title: "Succès",
        description: "Calcul sauvegardé avec succès",
      });

      // Reset form
      setFormData({
        montantFinancer: '',
        coefficientEmprunteur: '',
        coefficientCoEmprunteur: '',
        coefficientComplementaire: '',
        extensionGarantie: '',
        revision: ''
      });

      // Reload calculations list
      await loadCalculations();
      
    } catch (error) {
      toast({
        title: "Erreur",
        description: error.message,
        variant: "destructive"
      });
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteCalculation = async (calculationId) => {
    try {
      await calculationsAPI.deleteCalculation(calculationId);
      
      toast({
        title: "Succès",
        description: "Calcul supprimé avec succès",
      });

      // Reload calculations list
      await loadCalculations();
      
    } catch (error) {
      toast({
        title: "Erreur", 
        description: error.message,
        variant: "destructive"
      });
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Calculator className="h-8 w-8 text-blue-600 mr-3" />
            <h1 className="text-3xl font-bold text-gray-800">TPL FINANCE</h1>
          </div>
          <p className="text-gray-600">Calculateur de financement professionnel</p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Form Section */}
          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader className="bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-t-lg">
              <CardTitle className="flex items-center">
                <Euro className="h-5 w-5 mr-2" />
                Paramètres de financement
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-6">
              {/* Montant à financer */}
              <div className="space-y-2">
                <Label htmlFor="montant" className="text-sm font-medium text-gray-700">
                  Montant à financer (€)
                </Label>
                <Input
                  id="montant"
                  type="number"
                  placeholder="ex: 50000"
                  value={formData.montantFinancer}
                  onChange={(e) => handleInputChange('montantFinancer', e.target.value)}
                  className="text-lg"
                />
              </div>

              {/* Coefficients Section */}
              <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
                <h3 className="font-semibold text-gray-800 flex items-center">
                  <Users className="h-4 w-4 mr-2" />
                  Coefficients
                </h3>
                
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="coeffEmprunteur" className="text-sm text-gray-600">
                      Coefficient Emprunteur
                    </Label>
                    <Input
                      id="coeffEmprunteur"
                      type="number"
                      step="0.001"
                      placeholder="ex: 4.5"
                      value={formData.coefficientEmprunteur}
                      onChange={(e) => handleInputChange('coefficientEmprunteur', e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="coeffCoEmprunteur" className="text-sm text-gray-600">
                      Coefficient Co-Emprunteur
                    </Label>
                    <Input
                      id="coeffCoEmprunteur"
                      type="number"
                      step="0.001"
                      placeholder="ex: 2.5"
                      value={formData.coefficientCoEmprunteur}
                      onChange={(e) => handleInputChange('coefficientCoEmprunteur', e.target.value)}
                    />
                  </div>

                  <div className="space-y-2 md:col-span-2">
                    <Label htmlFor="coeffComplementaire" className="text-sm text-gray-600">
                      Coefficient Complémentaire
                    </Label>
                    <Input
                      id="coeffComplementaire"
                      type="number"
                      step="0.001"
                      placeholder="ex: 1.5"
                      value={formData.coefficientComplementaire}
                      onChange={(e) => handleInputChange('coefficientComplementaire', e.target.value)}
                    />
                  </div>
                </div>
              </div>

              {/* Montants fixes */}
              <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
                <h3 className="font-semibold text-gray-800 flex items-center">
                  <Shield className="h-4 w-4 mr-2" />
                  Montants fixes
                </h3>
                
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="extension" className="text-sm text-gray-600">
                      Extension de garantie (€)
                    </Label>
                    <Input
                      id="extension"
                      type="number"
                      placeholder="ex: 150"
                      value={formData.extensionGarantie}
                      onChange={(e) => handleInputChange('extensionGarantie', e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="revision" className="text-sm text-gray-600">
                      Révision (€)
                    </Label>
                    <Input
                      id="revision"
                      type="number"
                      placeholder="ex: 75"
                      value={formData.revision}
                      onChange={(e) => handleInputChange('revision', e.target.value)}
                    />
                  </div>
                </div>
              </div>

              <Button 
                onClick={handleSaveCalculation}
                className="w-full bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white"
                disabled={!formData.montantFinancer || calculations.mensualitesTotales === 0 || saving}
              >
                {saving ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <FileText className="h-4 w-4 mr-2" />
                )}
                {saving ? 'Sauvegarde...' : 'Sauvegarder ce calcul'}
              </Button>
            </CardContent>
          </Card>

          {/* Results Section */}
          <div className="space-y-6">
            {/* Live Calculations */}
            <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
              <CardHeader className="bg-gradient-to-r from-green-600 to-green-700 text-white rounded-t-lg">
                <CardTitle>Résultats du calcul</CardTitle>
              </CardHeader>
              <CardContent className="p-6 space-y-4">
                <div className="grid gap-3">
                  <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                    <span className="text-sm font-medium text-blue-800">Mensualité Emprunteur</span>
                    <span className="font-bold text-blue-900">{formatCurrency(calculations.mensualiteEmprunteur)}</span>
                  </div>
                  
                  <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                    <span className="text-sm font-medium text-blue-800">Mensualité Co-Emprunteur</span>
                    <span className="font-bold text-blue-900">{formatCurrency(calculations.mensualiteCoEmprunteur)}</span>
                  </div>
                  
                  <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                    <span className="text-sm font-medium text-blue-800">Complémentaire</span>
                    <span className="font-bold text-blue-900">{formatCurrency(calculations.complementaire)}</span>
                  </div>
                  
                  <div className="flex justify-between items-center p-3 bg-orange-50 rounded-lg">
                    <span className="text-sm font-medium text-orange-800">Extension de garantie</span>
                    <span className="font-bold text-orange-900">{formatCurrency(parseFloat(formData.extensionGarantie) || 0)}</span>
                  </div>
                  
                  <div className="flex justify-between items-center p-3 bg-orange-50 rounded-lg">
                    <span className="text-sm font-medium text-orange-800">Révision</span>
                    <span className="font-bold text-orange-900">{formatCurrency(parseFloat(formData.revision) || 0)}</span>
                  </div>
                  
                  <div className="flex justify-between items-center p-4 bg-gradient-to-r from-green-100 to-green-200 rounded-lg border-2 border-green-300">
                    <span className="text-lg font-bold text-green-800">MENSUALITÉS TOTALES</span>
                    <span className="text-xl font-bold text-green-900">{formatCurrency(calculations.mensualitesTotales)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Saved Calculations History */}
            <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
              <CardHeader className="bg-gradient-to-r from-gray-600 to-gray-700 text-white rounded-t-lg">
                <CardTitle>Historique des calculs</CardTitle>
              </CardHeader>
              <CardContent className="p-6">
                {loading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin mr-2" />
                    <span>Chargement...</span>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-80 overflow-y-auto">
                    {savedCalculations.length === 0 ? (
                      <p className="text-gray-500 text-center py-4">Aucun calcul sauvegardé</p>
                    ) : (
                      savedCalculations.map((calc) => (
                        <div key={calc.id} className="p-3 border border-gray-200 rounded-lg bg-gray-50">
                          <div className="flex justify-between items-start">
                            <div className="text-sm text-gray-600 flex-1">
                              <div className="font-medium">Date: {formatDate(calc.createdAt)}</div>
                              <div>Montant: {formatCurrency(parseFloat(calc.montantFinancer))}</div>
                              <div className="text-xs text-gray-500">
                                Coeff: {calc.coefficientEmprunteur}% / {calc.coefficientCoEmprunteur}% / {calc.coefficientComplementaire}%
                              </div>
                            </div>
                            <div className="text-right flex items-center gap-2">
                              <div>
                                <div className="text-sm font-bold text-green-700">
                                  {formatCurrency(calc.mensualitesTotales)}
                                </div>
                              </div>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDeleteCalculation(calc.id)}
                                className="text-red-600 hover:text-red-800 hover:bg-red-50 p-1 h-8 w-8"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FinanceCalculator;