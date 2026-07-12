<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const email = ref('')
const password = ref('')
const isLoading = ref(false)

const router = useRouter()
const authStore = useAuthStore()

const handleLogin = async () => {
    isLoading.value = true
    console.log('Sending data to the backend via axios')

    try {
        const response = await axios.post('http://127.0.0.1:5000/login', {
            email: email.value,
            password: password.value
        })

        authStore.login(response.data.access_token, response.data.role)

        // Redirect the user based on their role
        if (authStore.role == 'admin') {
            router.push('/admin-dashboard')
        } else if (authStore.role == 'staff') {
            router.push('/staff-dashboard')
        } else {
            router.push('/trekker-dashboard')
        }
    } catch (error) {
        if (error.response) {
            alert(`Login Failed: ${error.response.data.msg}`)
        } else {
            console.log("Connection error: ", error)
            alert("Could not connect to the server. Is Flask Running ?")
        }
    } finally {
        isLoading.value = false 
    }
}
</script>

<template>
    <main class="dashboard-bg d-flex align-items-center justify-content-center">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-5">
                    
                    <!-- Using the same neo-panel from your dashboards -->
                    <div class="neo-panel p-5 text-center">
                        <h2 class="mb-2 text-dark fw-bold">Trekker Basecamp</h2>
                        <p class="text-muted mb-4">Sign in to your account</p>

                        <form @submit.prevent="handleLogin">
                            <div class="mb-3 text-start">
                                <label class="form-label fw-bold text-secondary">Email Address</label>
                                <input type="email" class="form-control" v-model="email" placeholder="you@example.com" required />
                            </div>

                            <div class="mb-4 text-start">
                                <label class="form-label fw-bold text-secondary">Password</label>
                                <input type="password" class="form-control" v-model="password" placeholder="Enter your password" required />
                            </div>

                            <button type="submit" class="btn btn-primary w-100 rounded-pill fw-bold py-2 shadow-sm" :disabled="isLoading">
                                <span v-if="isLoading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                                <span v-else>Login</span>
                            </button>
                        </form>

                        <p class="mt-4 mb-0 text-muted">New here? 
                            <RouterLink to="/register" class="text-primary text-decoration-none fw-bold">Register here</RouterLink>
                        </p>
                    </div>

                </div>
            </div>
        </div>
    </main>
</template>

<style scoped>
.dashboard-bg {
    background-color: #e9e8f7; 
    min-height: 100vh; 
}

.neo-panel {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.7), rgba(248, 250, 252, 0.5));
    backdrop-filter: blur(12px); 
    border: 1px solid rgba(255, 255, 255, 0.8);
    border-radius: 16px;
    box-shadow: 8px 8px 16px #d1d9e6, -8px -8px 16px #ffffff;
}
</style>