'use client';

import React from "react";
import { TagTree } from "@/components/tag-tree";
import { TagProvider } from "@/contexts/tag-context";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle } from "lucide-react";
import { UserMenu } from '@/components/auth/user-menu';
import { ArrowLeft, Settings, BookOpen } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/auth-context';


export default function TagsManagerPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();

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
              <h1 className="text-xl font-bold text-gray-900">Tag Manager</h1>
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
        <Card className="mb-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-blue-600" />
            Tag Manager
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-gray-600">
          View the complete tag taxonomy and add or edit tags as your business needs evolve.
        </CardContent>
      </Card>

      <TagProvider>
        <TagTree />
      </TagProvider>
        </main>        
      
    </div>
  );
}
