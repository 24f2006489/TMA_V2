import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', () => {
    // 1. STATE (The Memory)
    // We try to grab the token from the browser's local storage first. 
    // If it's not there, it defaults to null.
    const token = ref(localStorage.getItem('token') || null)
    const role = ref(localStorage.getItem('role') || null)

    // 2. ACTIONS (Functions to change the memory)
    const login = (newToken, newRole) => {
        token.value = newToken;
        role.value = newRole;

        localStorage.setItem('token', newToken);
        localStorage.setItem('role', newRole);
    }
    
    const logout = () => {
        token.value = null,
        role.value = null
        
        localStorage.removeItem('token')
        localStorage.removeItem('role')
    }
    // 3. RETURN
    // We expose these so our components can actually use them.
    return { token, role, login, logout }
})