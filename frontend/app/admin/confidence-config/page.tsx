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
  const [thresholds, setThresholds] = useState<ThresholdConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingInitial, setLoadingInitial] = useState(true);
  const { toast } = useToast();

  const handleThresholdChange = (level: keyof ThresholdConfig, value: string) => {
    const numValue = parseFloat(value);
    if (!isNaN(numValue) && numValue >= 0 && numValue <= 1 && thresholds) {
      setThresholds(prev => prev ? ({
        ...prev,
        [level]: numValue
      }) : null);
    }
  };

  const updateConfig = async () => {
    if (!thresholds) {
      toast({
        title: "Error",
        description: "No configuration loaded to save.",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      await apiClient.updateConfidenceThresholds(thresholds);
      toast({
        title: "Configuration Updated",
        description: "Confidence thresholds have been saved to the database.",
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Unknown error occurred";
      toast({
        title: "Failed to Update Configuration",
        description: `Database update failed: ${errorMessage}`,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const resetToDefaults = () => {
    setThresholds({
      primary: 0.85,
      secondary: 0.80,
      tertiary: 0.75
    });
    toast({
      title: "Values Reset",
      description: "Thresholds reset to default values. Click 'Save Configuration' to persist to database.",
    });
  };

  useEffect(() => {
    // Load config on mount - only from database
    const loadConfig = async () => {
      try {
        const apiThresholds = await apiClient.getConfidenceThresholds();
        setThresholds(apiThresholds);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "Unknown error occurred";
        console.error('Failed to load confidence thresholds from database:', error);
        toast({
          title: "Failed to Load Configuration",
          description: `Unable to load thresholds from database: ${errorMessage}`,
          variant: "destructive",
        });
        // Leave thresholds as null to show that no data was loaded
        setThresholds(null);
      } finally {
        setLoadingInitial(false);
      }
    };
    
    loadConfig();
  }, [toast]);

  if (loadingInitial) {
    return (
      <div className="container mx-auto p-6 max-w-2xl">
        <Card>
          <CardContent className="p-8 text-center">
            <div className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mx-auto mb-4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2 mx-auto"></div>
            </div>
            <p className="mt-4 text-gray-600">Loading configuration from database...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (thresholds === null) {
    return (
      <div className="container mx-auto p-6 max-w-2xl">
        <Card>
          <CardHeader>
            <CardTitle>Confidence Threshold Configuration</CardTitle>
            <CardDescription>
              Configure when the orchestrator should fall back to LLM service based on AI confidence scores.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="p-6 border border-red-200 bg-red-50 rounded-lg text-center">
              <p className="text-red-800 font-semibold mb-2">Configuration Not Available</p>
              <p className="text-red-700 text-sm mb-4">
                Unable to load confidence thresholds from the database. Please check:
              </p>
              <ul className="text-red-700 text-sm text-left max-w-md mx-auto space-y-1">
                <li>• Prediction service is running</li>
                <li>• Database connection is working</li>
                <li>• Supabase credentials are configured</li>
                <li>• Confidence thresholds table exists</li>
              </ul>
              <Button 
                className="mt-4"
                onClick={() => window.location.reload()}
                variant="outline"
              >
                Retry Loading
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

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
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-green-800 text-sm">
              ✅ Configuration loaded from database successfully
            </p>
          </div>
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

          <div className="p-4 border border-blue-200 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>Database Storage:</strong> Configuration is stored in the Supabase database 
              and persisted across all prediction service instances. Changes take effect immediately 
              for all new classification requests.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}