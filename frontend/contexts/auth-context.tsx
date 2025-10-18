'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import { User } from '@supabase/supabase-js'
import { createClient } from '@/lib/supabase/client'
import { AuthContextType, UserProfile, UserPreferences } from '@/lib/auth/types'

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [preferences, setPreferences] = useState<UserPreferences | null>(null)
  const [loading, setLoading] = useState(true)
  const supabase = createClient()

  useEffect(() => {
    const getInitialSession = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession()

        if (session?.user) {
          setUser(session.user)
          // Fetch profile/preferences in background without blocking loading
          fetchUserProfile(session.user.id).catch(console.error)
          fetchUserPreferences(session.user.id).catch(console.error)
        }
      } catch (error) {
        console.error('Error getting initial session:', error)
      } finally {
        setLoading(false)
      }
    }

    getInitialSession()

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        // console.log('Auth state change:', event, !!session?.user)

        if (session?.user) {
          setUser(session.user)
          // Fetch profile/preferences in background
          fetchUserProfile(session.user.id).catch(console.error)
          fetchUserPreferences(session.user.id).catch(console.error)
        } else {
          setUser(null)
          setProfile(null)
          setPreferences(null)
        }

        // Don't set loading to false here for sign out to avoid flash
        if (event !== 'SIGNED_OUT') {
          setLoading(false)
        }
      }
    )

    return () => subscription.unsubscribe()
  }, [])

  const fetchUserProfile = async (userId: string) => {
    try {
      const { data, error } = await supabase
        .from('users')
        .select('*')
        .eq('id', userId)
        .single()

      if (error) {
        console.error('Error fetching user profile:', error)
        // Don't return, continue to set loading to false
        setProfile(null)
        return
      }

      setProfile(data)
    } catch (error) {
      console.error('Error fetching user profile:', error)
      setProfile(null)
    }
  }

  const fetchUserPreferences = async (userId: string) => {
    try {
      const { data, error } = await supabase
        .from('user_preferences')
        .select('*')
        .eq('user_id', userId)
        .single()

      if (error) {
        console.error('Error fetching user preferences:', error)
        // Don't return, continue to set loading to false
        setPreferences(null)
        return
      }

      setPreferences(data)
    } catch (error) {
      console.error('Error fetching user preferences:', error)
      setPreferences(null)
    }
  }

  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (!error) {
      // Handle redirect after successful login
      const urlParams = new URLSearchParams(window.location.search)
      const redirectTo = urlParams.get('redirectTo') || '/'
      window.location.href = redirectTo
    }

    return { error }
  }

  const signUp = async (email: string, password: string, fullName?: string) => {
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: fullName,
        }
      }
    })
    return { error }
  }

  const signOut = async () => {
    try {
      // Clear local state immediately for faster UI response
      setUser(null)
      setProfile(null)
      setPreferences(null)
      setLoading(false)

      // Sign out from Supabase
      await supabase.auth.signOut()

      // Redirect to login page
      window.location.href = '/login'
    } catch (error) {
      console.error('Error signing out:', error)
      // Still redirect even if there's an error
      window.location.href = '/login'
    }
  }

  const updateProfile = async (updates: Partial<UserProfile>) => {
    if (!user) return { error: 'No user logged in' }

    const { error } = await supabase
      .from('users')
      .update(updates)
      .eq('id', user.id)

    if (!error && profile) {
      setProfile({ ...profile, ...updates })
    }

    return { error }
  }

  const updatePreferences = async (updates: Partial<UserPreferences>) => {
    if (!user) return { error: 'No user logged in' }

    const { error } = await supabase
      .from('user_preferences')
      .update(updates)
      .eq('user_id', user.id)

    if (!error && preferences) {
      setPreferences({ ...preferences, ...updates })
    }

    return { error }
  }

  const value: AuthContextType = {
    user,
    profile,
    preferences,
    loading,
    signIn,
    signUp,
    signOut,
    updateProfile,
    updatePreferences,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}