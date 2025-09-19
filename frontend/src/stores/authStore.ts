import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: number
  wr_vid: string
  wr_name: string
  wr_avatar: string
}

interface AuthState {
  token: string | null
  user: User | null
  setAuth: (token: string, user: User) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    {
      name: 'weread-auth',
    }
  )
)