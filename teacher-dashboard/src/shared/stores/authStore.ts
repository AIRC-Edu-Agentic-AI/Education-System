import { create } from 'zustand'

const NAMESPACE = 'https://agentic-teacher.vnu.edu.vn'

export interface AuthUser {
  email: string
  name: string
  role: string
  modules: string[]
  presentations: string[]
  years: string[]
  assigned_to: string[]
}

interface AuthStore {
  user: AuthUser | null
  setUserFromAuth0: (auth0User: any, idTokenClaims: any) => void
  clearUser: () => void
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  setUserFromAuth0: (auth0User, idTokenClaims) => {
    const user: AuthUser = {
      email: auth0User.email || '',
      name: auth0User.name || '',
      role: idTokenClaims?.[`${NAMESPACE}/role`] || null,
      modules: idTokenClaims?.[`${NAMESPACE}/modules`] || [],
      presentations: idTokenClaims?.[`${NAMESPACE}/presentations`] || [],
      years: idTokenClaims?.[`${NAMESPACE}/years`] || [],
      assigned_to: idTokenClaims?.[`${NAMESPACE}/assigned_to`] || [],
    }
    set({ user })
  },
  clearUser: () => set({ user: null }),
}))