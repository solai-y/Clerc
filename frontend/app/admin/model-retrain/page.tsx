'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { apiClient } from '@/lib/api';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { ArrowLeft, Settings, BookOpen, Tags } from 'lucide-react';
import { UserMenu } from '@/components/auth/user-menu';
import { useAuth } from '@/contexts/auth-context';

interface ValidationResult {
  valid: boolean;
  total_documents: number;
  primary_tags: Record<string, number>;
  secondary_tags: Record<string, number>;
  tertiary_tags: Record<string, number>;
  invalid_tags: Array<{ level: string; tag: string; count: number; required: number }>;
  message: string;
}

interface NewTagsInfo {
  hasNewTags: boolean;
  newPrimaryTags: string[];
  newSecondaryTags: string[];
  newTertiaryTags: string[];
  totalNewTags: number;
}

export default function ModelRetrainPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [validationBeforeRetrain, setValidationBeforeRetrain] = useState<ValidationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [validating, setValidating] = useState(true);
  const [retraining, setRetraining] = useState(false);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [retrainProgress, setRetrainProgress] = useState(0);
  const [retrainStatus, setRetrainStatus] = useState<'idle' | 'in_progress' | 'completed' | 'failed'>('idle');
  const [retrainMessage, setRetrainMessage] = useState('');
  const [newTagsInfo, setNewTagsInfo] = useState<NewTagsInfo | null>(null);
  const [showNewTagsDialog, setShowNewTagsDialog] = useState(false);
  const { toast } = useToast();

  const getApiDocsUrl = () => {
    if (typeof window !== 'undefined') {
      const currentOrigin = window.location.origin;
      if (currentOrigin.includes('localhost') || currentOrigin.includes('127.0.0.1')) {
        return 'http://localhost:8000/docs';
      }
      return 'https://clercbackend.clerc.uk/docs';
    }
    return 'http://localhost:8000/docs';
  };

  // Function to compare tags and find new ones
  const compareTagsAndFindNew = (oldValidation: ValidationResult, newValidation: ValidationResult): NewTagsInfo => {
    const oldPrimaryTags = Object.keys(oldValidation.primary_tags);
    const newPrimaryTags = Object.keys(newValidation.primary_tags);
    const addedPrimaryTags = newPrimaryTags.filter(tag => !oldPrimaryTags.includes(tag));

    const oldSecondaryTags = Object.keys(oldValidation.secondary_tags);
    const newSecondaryTags = Object.keys(newValidation.secondary_tags);
    const addedSecondaryTags = newSecondaryTags.filter(tag => !oldSecondaryTags.includes(tag));

    const oldTertiaryTags = Object.keys(oldValidation.tertiary_tags);
    const newTertiaryTags = Object.keys(newValidation.tertiary_tags);
    const addedTertiaryTags = newTertiaryTags.filter(tag => !oldTertiaryTags.includes(tag));

    const totalNewTags = addedPrimaryTags.length + addedSecondaryTags.length + addedTertiaryTags.length;

    return {
      hasNewTags: totalNewTags > 0,
      newPrimaryTags: addedPrimaryTags,
      newSecondaryTags: addedSecondaryTags,
      newTertiaryTags: addedTertiaryTags,
      totalNewTags
    };
  };

  // Function to check rebuild status
  const checkRebuildStatus = useCallback(async () => {
    try {
      const status = await apiClient.getRebuildStatus();
      return status;
    } catch (error) {
      console.error('Failed to check rebuild status:', error);
      return null;
    }
  }, []);

  // Function to validate training data
  const validateTrainingData = async () => {
    setValidating(true);
    try {
      const result = await apiClient.validateTrainingData();
      setValidation(result);

      if (!result.valid) {
        toast({
          title: "Validation Failed",
          description: result.message,
          variant: "destructive",
        });
      } else {
        toast({
          title: "Validation Passed",
          description: `Training data is valid with ${result.total_documents} documents.`,
        });
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Unknown error occurred";

      // Check if error is 502 Bad Gateway (AI service still loading)
      if (errorMessage.includes("502") || errorMessage.includes("Bad Gateway")) {
        toast({
          title: "AI Service Loading",
          description: "The AI service is still loading models on startup. This usually takes 2-3 minutes. Please wait and try again.",
          variant: "default",
        });
      } else {
        toast({
          title: "Validation Error",
          description: `Failed to validate training data: ${errorMessage}`,
          variant: "destructive",
        });
      }
      setValidation(null);
    } finally {
      setValidating(false);
    }
  };

  // Initial validation on mount
  useEffect(() => {
    validateTrainingData();
  }, []);

  // Poll for retrain status
  useEffect(() => {
    if (!retraining) return;

    const pollInterval = setInterval(async () => {
      const rebuildStatus = await checkRebuildStatus();

      if (!rebuildStatus) {
        // Failed to get status, keep polling
        return;
      }

      // Update progress and message from backend
      setRetrainProgress(rebuildStatus.progress);
      setRetrainMessage(rebuildStatus.message);

      if (rebuildStatus.status === 'completed' && retrainStatus === 'in_progress') {
        // Retraining completed successfully
        setRetraining(false);
        setRetrainStatus('completed');
        setRetrainProgress(100);
        setRetrainMessage(rebuildStatus.message || 'Model retraining completed successfully!');

        toast({
          title: "Retraining Complete",
          description: rebuildStatus.duration_seconds
            ? `Model retrained successfully in ${rebuildStatus.duration_seconds}s`
            : "The model has been successfully retrained and is now active.",
        });

        // Revalidate training data and compare tags
        setTimeout(async () => {
          try {
            const newValidation = await apiClient.validateTrainingData();
            setValidation(newValidation);

            // Compare with pre-retrain validation if available
            if (validationBeforeRetrain) {
              const tagsComparison = compareTagsAndFindNew(validationBeforeRetrain, newValidation);
              setNewTagsInfo(tagsComparison);

              // Show dialog with results
              setShowNewTagsDialog(true);
            }
          } catch (error) {
            console.error('Failed to revalidate after retrain:', error);
          }
        }, 1000);
      } else if (rebuildStatus.status === 'failed' && retrainStatus === 'in_progress') {
        // Retraining failed
        setRetraining(false);
        setRetrainStatus('failed');
        setRetrainProgress(0);
        setRetrainMessage(rebuildStatus.error || 'Model retraining failed');

        toast({
          title: "Retraining Failed",
          description: rebuildStatus.error || "An error occurred during model retraining.",
          variant: "destructive",
        });
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [retraining, retrainStatus, validationBeforeRetrain, checkRebuildStatus, toast]);

  // Handle retrain button click
  const handleRetrainClick = () => {
    if (!validation) {
      toast({
        title: "Cannot Retrain",
        description: "Training data has not been validated yet.",
        variant: "destructive",
      });
      return;
    }

    setShowConfirmDialog(true);
  };

  // Handle confirmed retrain
  const handleConfirmedRetrain = async () => {
    setShowConfirmDialog(false);
    setLoading(true);
    setRetraining(true);
    setRetrainStatus('in_progress');
    setRetrainProgress(0);
    setRetrainMessage('Initializing model retraining...');

    // Save current validation state to compare later
    if (validation) {
      setValidationBeforeRetrain(validation);
    }

    try {
      const result = await apiClient.triggerModelRetrain();

      toast({
        title: "Retraining Started",
        description: "Model retraining has been initiated. Polling for real-time progress...",
      });

      setRetrainMessage('Waiting for rebuild status...');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Unknown error occurred";
      setRetraining(false);
      setRetrainStatus('failed');
      setRetrainMessage(`Retraining failed: ${errorMessage}`);

      toast({
        title: "Retraining Failed",
        description: `Failed to start model retraining: ${errorMessage}`,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  if (validating) {
    return (
      <div className="min-h-screen bg-white">
        {/* Header */}
        <header className="border-b border-gray-200 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <h1 className="text-5xl font-bold text-red-600" style={{ marginLeft: "1rem" }}>
                  Clerc.
                </h1>
                <div className="h-6 w-px bg-gray-300 mx-4" />
                <h1 className="text-xl font-bold text-gray-900">Model Retraining</h1>
              </div>

              <div className="flex items-center gap-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => router.push('/')}
                  className="flex items-center gap-2"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Back to Documents</span>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => window.open(getApiDocsUrl(), '_blank')}
                  className="flex items-center gap-2"
                >
                  <BookOpen className="w-4 h-4" />
                  <span>API Docs</span>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => router.push('/admin/confidence-config')}
                  className="flex items-center gap-2"
                >
                  <Settings className="w-4 h-4" />
                  <span>Confidence Config</span>
                </Button>
                <Button
                variant="outline"
                size="sm"
                onClick={() => router.push("/tag-manager")}
                className="flex items-center gap-2"
              >
                <Tags className="w-4 h-4" />
                <span>Tag Manager</span>
              </Button>
                {authLoading ? (
                  <div className="w-8 h-8 animate-pulse bg-gray-200 rounded-full" />
                ) : user ? (
                  <UserMenu />
                ) : null}
              </div>
            </div>
          </div>
        </header>

        <main className="max-w-4xl mx-auto p-6">
          <Card>
            <CardContent className="p-8 text-center">
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mx-auto mb-4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2 mx-auto"></div>
              </div>
              <p className="mt-4 text-gray-600">Validating training data...</p>
            </CardContent>
          </Card>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-5xl font-bold text-red-600" style={{ marginLeft: "1rem" }}>
                Clerc.
              </h1>
              <div className="h-6 w-px bg-gray-300 mx-4" />
              <h1 className="text-xl font-bold text-gray-900">Model Retraining</h1>
            </div>

            <div className="flex items-center gap-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push('/')}
                className="flex items-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Back to Documents</span>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.open(getApiDocsUrl(), '_blank')}
                className="flex items-center gap-2"
              >
                <BookOpen className="w-4 h-4" />
                <span>API Docs</span>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push('/admin/confidence-config')}
                className="flex items-center gap-2"
              >
                <Settings className="w-4 h-4" />
                <span>Confidence Config</span>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push("/tag-manager")}
                className="flex items-center gap-2"
              >
                <Tags className="w-4 h-4" />
                <span>Tag Manager</span>
              </Button>
              {authLoading ? (
                <div className="w-8 h-8 animate-pulse bg-gray-200 rounded-full" />
              ) : user ? (
                <UserMenu />
              ) : null}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto p-6">
        <Card>
          <CardHeader>
            <CardTitle>Model Retraining</CardTitle>
            <CardDescription>
              Retrain the AI classification model with updated training data. Ensure all tags have sufficient training documents before proceeding.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
          {/* Validation Status */}
          {validation && (
            <Alert variant={validation.valid ? "default" : "default"}>
              <AlertTitle>
                {validation.valid
                  ? "✓ Training Data Valid - Ready to Retrain"
                  : `⚠ ${validation.invalid_tags.length} Tag${validation.invalid_tags.length > 1 ? 's' : ''} Will Be Excluded`}
              </AlertTitle>
              <AlertDescription>
                {validation.valid
                  ? `All ${Object.keys(validation.primary_tags).length + Object.keys(validation.secondary_tags).length + Object.keys(validation.tertiary_tags).length} tags have sufficient training data (≥10 documents).`
                  : `Tags with fewer than 10 documents will be excluded from retraining. The model will be trained with the remaining valid tags.`}
              </AlertDescription>
            </Alert>
          )}

          {/* Training Statistics */}
          {validation && (
            <Card>
              <CardHeader>
                <CardTitle>Training Data Statistics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-blue-50 rounded-lg">
                  <p className="text-lg font-semibold">Total Documents: {validation.total_documents}</p>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Primary Tags</p>
                    <p className="text-xl font-bold">{Object.keys(validation.primary_tags).length}</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Secondary Tags</p>
                    <p className="text-xl font-bold">{Object.keys(validation.secondary_tags).length}</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Tertiary Tags</p>
                    <p className="text-xl font-bold">{Object.keys(validation.tertiary_tags).length}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Excluded Tags Warning */}
          {validation && !validation.valid && validation.invalid_tags.length > 0 && (
            <Card className="border-orange-200 bg-orange-50">
              <CardHeader>
                <CardTitle className="text-orange-800">Tags Excluded from Retraining</CardTitle>
                <CardDescription className="text-orange-700">
                  The following tags have fewer than 10 training documents and will be excluded from the retrained model:
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {validation.invalid_tags.map((tag, index) => (
                    <div key={index} className="flex justify-between items-center p-2 bg-white rounded border border-orange-200">
                      <div>
                        <span className="font-semibold">{tag.tag}</span>
                        <span className="text-sm text-gray-600 ml-2">({tag.level})</span>
                      </div>
                      <div className="text-sm text-orange-700">
                        {tag.count} / {tag.required} documents
                      </div>
                    </div>
                  ))}
                </div>
                <p className="text-sm text-orange-700 mt-4">
                  <strong>Note:</strong> These tags will not be available in the retrained model. Add more training documents for these tags to include them in future retraining.
                </p>
              </CardContent>
            </Card>
          )}

          {/* Retrain Progress (AC3) */}
          {retrainStatus !== 'idle' && (
            <Card>
              <CardHeader>
                <CardTitle>Retraining Status</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>{retrainMessage}</span>
                    <span>{retrainProgress}%</span>
                  </div>
                  <Progress value={retrainProgress} />
                </div>

                {retrainStatus === 'in_progress' && (
                  <Alert>
                    <AlertTitle>Training in Progress</AlertTitle>
                    <AlertDescription>
                      The model is being retrained. You can continue using the application with the current model. The new model will be activated automatically upon completion.
                    </AlertDescription>
                  </Alert>
                )}

                {retrainStatus === 'completed' && (
                  <Alert>
                    <AlertTitle>Retraining Successful</AlertTitle>
                    <AlertDescription>
                      The model has been successfully retrained and is now active. All new predictions will use the updated model.
                    </AlertDescription>
                  </Alert>
                )}

                {retrainStatus === 'failed' && (
                  <Alert variant="destructive">
                    <AlertTitle>Retraining Failed</AlertTitle>
                    <AlertDescription>
                      {retrainMessage}
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          )}

            {/* Actions (AC1) */}
            <div className="flex gap-3">
              <Button
                onClick={handleRetrainClick}
                disabled={!validation || loading || retraining}
                size="lg"
              >
                {retraining ? 'Retraining...' : 'Retrain Model'}
              </Button>
              <Button
                variant="outline"
                onClick={validateTrainingData}
                disabled={validating || retraining}
              >
                {validating ? 'Validating...' : 'Revalidate Data'}
              </Button>
            </div>

            {/* Information */}
            <Card className="border-blue-200 bg-blue-50">
              <CardContent className="p-4">
                <p className="text-sm text-blue-800">
                  <strong>Note:</strong> Model retraining is a background process that typically takes 5-15 minutes depending on the size of your training data. The current model will continue to serve predictions during retraining, and will be automatically replaced when the new model is ready.
                </p>
              </CardContent>
            </Card>
          </CardContent>
        </Card>

        {/* Confirmation Dialog (AC2) */}
        <AlertDialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Confirm Model Retraining</AlertDialogTitle>
              <AlertDialogDescription asChild>
                <div>
                  <p className="mb-2">Are you sure you want to retrain the AI classification model? This process will:</p>
                  <ul className="list-disc ml-6 mt-2 space-y-1">
                    <li>Train a new model using {validation?.total_documents} documents</li>
                    {validation && !validation.valid && validation.invalid_tags.length > 0 && (
                      <li className="text-orange-700 font-semibold">
                        Exclude {validation.invalid_tags.length} tag{validation.invalid_tags.length > 1 ? 's' : ''} with insufficient training data ({"<"}10 documents)
                      </li>
                    )}
                    <li>Take approximately 5-15 minutes to complete</li>
                    <li>Keep the current model active during retraining</li>
                    <li>Automatically activate the new model when ready</li>
                  </ul>
                </div>
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={handleConfirmedRetrain}>
                Confirm Retrain
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        {/* New Tags Detection Dialog */}
        <AlertDialog open={showNewTagsDialog} onOpenChange={setShowNewTagsDialog}>
          <AlertDialogContent className="max-w-2xl">
            <AlertDialogHeader>
              <AlertDialogTitle>
                {newTagsInfo?.hasNewTags ? '🎉 New Tags Detected!' : '✓ Retraining Complete'}
              </AlertDialogTitle>
              <AlertDialogDescription asChild>
                <div>
                  {newTagsInfo?.hasNewTags ? (
                    <div className="space-y-4">
                      <p className="text-green-700 font-semibold">
                        {newTagsInfo.totalNewTags} new tag{newTagsInfo.totalNewTags > 1 ? 's have' : ' has'} been added to the model!
                      </p>

                      {newTagsInfo.newPrimaryTags.length > 0 && (
                        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                          <p className="font-semibold text-blue-900 mb-2">
                            Primary Tags ({newTagsInfo.newPrimaryTags.length})
                          </p>
                          <div className="flex flex-wrap gap-2">
                            {newTagsInfo.newPrimaryTags.map((tag) => (
                              <span key={tag} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                                {tag}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {newTagsInfo.newSecondaryTags.length > 0 && (
                        <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                          <p className="font-semibold text-green-900 mb-2">
                            Secondary Tags ({newTagsInfo.newSecondaryTags.length})
                          </p>
                          <div className="flex flex-wrap gap-2">
                            {newTagsInfo.newSecondaryTags.map((tag) => (
                              <span key={tag} className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                                {tag}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {newTagsInfo.newTertiaryTags.length > 0 && (
                        <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
                          <p className="font-semibold text-purple-900 mb-2">
                            Tertiary Tags ({newTagsInfo.newTertiaryTags.length})
                          </p>
                          <div className="flex flex-wrap gap-2">
                            {newTagsInfo.newTertiaryTags.map((tag) => (
                              <span key={tag} className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium">
                                {tag}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      <p className="text-sm text-gray-600 mt-4">
                        These new tags now have at least 10 training documents and have been included in the retrained model.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <p className="text-gray-700">
                        Model retraining completed successfully! No new tags were added.
                      </p>
                      <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
                        <p className="text-sm text-gray-600">
                          This typically happens when:
                        </p>
                        <ul className="list-disc ml-6 mt-2 text-sm text-gray-600 space-y-1">
                          <li>New tags don't have enough training documents (minimum 10 required)</li>
                          <li>The training data hasn't changed since the last retraining</li>
                          <li>Existing tag distributions were updated without adding new tags</li>
                        </ul>
                      </div>
                    </div>
                  )}
                </div>
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogAction onClick={() => setShowNewTagsDialog(false)}>
                Got it!
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </main>
    </div>
  );
}
