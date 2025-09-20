'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { apiClient } from '@/lib/api';

interface ThresholdConfig {
  primary: number;
  secondary: number;
  tertiary: number;
}

export default function ConfidenceConfigPage() {
  const [thresholds, setThresholds] = useState<ThresholdConfig>({
    primary: 0.90,
    secondary: 0.85,
    tertiary: 0.80
  });
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleThresholdChange = (level: keyof ThresholdConfig, value: string) => {
    const numValue = parseFloat(value);
    if (!isNaN(numValue) && numValue >= 0 && numValue <= 1) {
      setThresholds(prev => ({
        ...prev,
        [level]: numValue
      }));
    }
  };

  const updateConfig = async () => {
    setLoading(true);
    try {
      // Try to update via API first
      try {
        await apiClient.updateConfidenceThresholds(thresholds);
        toast({
          title: "Configuration Updated",
          description: "Confidence thresholds have been saved to the backend.",
        });
      } catch (apiError) {
        // Fallback to localStorage if API not available
        localStorage.setItem('confidence_thresholds', JSON.stringify(thresholds));
        toast({
          title: "Configuration Updated (Local)",
          description: "Thresholds saved locally. Backend API not available.",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update configuration.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const resetToDefaults = () => {
    setThresholds({
      primary: 0.90,
      secondary: 0.85,
      tertiary: 0.80
    });
    localStorage.removeItem('confidence_thresholds');
    toast({
      title: "Reset Complete",
      description: "Thresholds reset to default values.",
    });
  };

  useEffect(() => {
    // Load config on mount - try API first, fallback to localStorage
    const loadConfig = async () => {
      try {
        const apiThresholds = await apiClient.getConfidenceThresholds();
        setThresholds(apiThresholds);
      } catch (apiError) {
        // Fallback to localStorage
        const saved = localStorage.getItem('confidence_thresholds');
        if (saved) {
          try {
            setThresholds(JSON.parse(saved));
          } catch (error) {
            console.error('Failed to parse saved thresholds:', error);
          }
        }
      }
    };
    
    loadConfig();
  }, []);

  return (
    <div className="container mx-auto p-6 max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle>Confidence Threshold Configuration</CardTitle>
          <CardDescription>
            Configure when the orchestrator should fall back to LLM service based on AI confidence scores.
            Lower thresholds mean more frequent LLM usage.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-4">
            <div className="space-y-2">
              <Label htmlFor="primary">Primary Classification Threshold</Label>
              <Input
                id="primary"
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={thresholds.primary}
                onChange={(e) => handleThresholdChange('primary', e.target.value)}
                placeholder="0.90"
              />
              <p className="text-sm text-muted-foreground">
                Current: {(thresholds.primary * 100).toFixed(0)}% - If primary confidence is below this, LLM will handle all levels
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="secondary">Secondary Classification Threshold</Label>
              <Input
                id="secondary"
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={thresholds.secondary}
                onChange={(e) => handleThresholdChange('secondary', e.target.value)}
                placeholder="0.85"
              />
              <p className="text-sm text-muted-foreground">
                Current: {(thresholds.secondary * 100).toFixed(0)}% - If secondary confidence is below this, LLM will handle secondary and tertiary
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="tertiary">Tertiary Classification Threshold</Label>
              <Input
                id="tertiary"
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={thresholds.tertiary}
                onChange={(e) => handleThresholdChange('tertiary', e.target.value)}
                placeholder="0.80"
              />
              <p className="text-sm text-muted-foreground">
                Current: {(thresholds.tertiary * 100).toFixed(0)}% - If tertiary confidence is below this, LLM will handle tertiary only
              </p>
            </div>
          </div>

          <div className="flex gap-3">
            <Button 
              onClick={updateConfig} 
              disabled={loading}
            >
              {loading ? 'Saving...' : 'Save Configuration'}
            </Button>
            <Button 
              variant="outline" 
              onClick={resetToDefaults}
            >
              Reset to Defaults
            </Button>
          </div>

          <div className="p-4 bg-muted rounded-lg">
            <h4 className="font-semibold mb-2">Current Configuration</h4>
            <div className="text-sm space-y-1">
              <p>Primary: {(thresholds.primary * 100).toFixed(1)}%</p>
              <p>Secondary: {(thresholds.secondary * 100).toFixed(1)}%</p>
              <p>Tertiary: {(thresholds.tertiary * 100).toFixed(1)}%</p>
            </div>
          </div>

          <div className="p-4 border border-amber-200 bg-amber-50 rounded-lg">
            <p className="text-sm text-amber-800">
              <strong>Note:</strong> This configuration is stored locally. For production use, 
              these values should be sent to the backend API and stored in the prediction service configuration.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}