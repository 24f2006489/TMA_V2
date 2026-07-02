<script setup>
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const handleLogout = () => {
    authStore.logout() // Wipes Pinia and localStorage!
    router.push('/login')
}
</script>

<template>
    <main>
        <h1>Super Secret Admin Dashboard</h1>
        <p>Welcome! Your role is: {{ authStore.role }}</p>

        <button @click="handleLogout">Logout</button>
    </main>
</template>