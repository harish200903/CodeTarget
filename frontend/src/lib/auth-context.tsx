"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { User, TokenResponse, apiRequest } from "./api";
import { useRouter } from "next/navigation";

interface AuthContextType {
  user: User | null;
  accessToken: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (fullName: string, email: string, password: string, confirmPassword: string) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const router = useRouter();

  // Try restoring session via refresh token cookie on mount
  useEffect(() => {
    async function restoreSession() {
      try {
        const data = await apiRequest<TokenResponse>("/api/v1/auth/refresh", {
          method: "POST",
        });
        setAccessToken(data.access_token);
        setUser(data.user);
      } catch (err) {
        setAccessToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    }
    restoreSession();
  }, []);

  const login = async (email: string, password: string) => {
    const data = await apiRequest<TokenResponse>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setAccessToken(data.access_token);
    setUser(data.user);

    if (!data.user.onboarding_completed) {
      router.push("/onboarding");
    } else {
      router.push("/dashboard");
    }
  };

  const register = async (
    fullName: string,
    email: string,
    password: string,
    confirmPassword: string
  ) => {
    const data = await apiRequest<TokenResponse>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({
        full_name: fullName,
        email,
        password,
        confirm_password: confirmPassword,
      }),
    });
    setAccessToken(data.access_token);
    setUser(data.user);
    router.push("/onboarding");
  };

  const logout = async () => {
    try {
      await apiRequest("/api/v1/auth/logout", { method: "POST" });
    } catch (e) {
      // Ignore logout errors
    } finally {
      setAccessToken(null);
      setUser(null);
      router.push("/login");
    }
  };

  const updateUser = (updatedUser: User) => {
    setUser(updatedUser);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        loading,
        login,
        register,
        logout,
        updateUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
