<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const name = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const contactDetails = ref('')
const emergencyContact = ref('')
const isLoading = ref(false)

const router = useRouter()

const handleRegister = async () => {
    if (password.value !== confirmPassword.value) {
        alert("Passwords do not match. Please re-check and try again.")
        return
    }

    isLoading.value = true

    try {
        const response = await axios.post('http://127.0.0.1:5000/register', {
            email: email.value,
            password: password.value,
            name: name.value,
            contact_details: contactDetails.value,
            emergency_contact: emergencyContact.value
        })

        alert(response.data.msg) 
        router.push('/login')
    } catch (error) {
        if (error.response) {
            alert(`Registration Failed: ${error.response.data.msg}`)
        } else {
            console.log("Connection error: ", error)
            alert("Could not connect to the server. Is Flask running?")
        }
    } finally {
        isLoading.value = false
    }
}
</script>

<template>
    <main class="dashboard-bg d-flex align-items-center justify-content-center py-5">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-7">
                    
                    <div class="neo-panel p-4 p-md-5">
                        <h2 class="text-center mb-2 text-dark fw-bold">Create Account</h2>
                        <p class="text-center text-muted mb-4">Join Trekker Basecamp in minutes</p>

                        <form @submit.prevent="handleRegister" class="row g-3">
                            <div class="col-md-12">
                                <label class="form-label fw-bold text-secondary mb-1">Full Name</label>
                                <input type="text" class="form-control" v-model="name" placeholder="John Doe" required />
                            </div>
                            
                            <div class="col-md-12">
                                <label class="form-label fw-bold text-secondary mb-1">Email Address</label>
                                <input type="email" class="form-control" v-model="email" placeholder="you@example.com" required />
                            </div>
                            
                            <div class="col-md-6">
                                <label class="form-label fw-bold text-secondary mb-1">Password</label>
                                <input type="password" class="form-control" v-model="password" placeholder="Min 6 characters" required minlength="6" />
                            </div>
                            
                            <div class="col-md-6">
                                <label class="form-label fw-bold text-secondary mb-1">Confirm Password</label>
                                <input type="password" class="form-control" v-model="confirmPassword" placeholder="Re-enter password" required minlength="6" />
                            </div>
                            
                            <div class="col-md-6">
                                <label class="form-label fw-bold text-secondary mb-1">Contact Number</label>
                                <input type="tel" class="form-control" v-model="contactDetails" placeholder="+91 98765 43210" required />
                            </div>
                            
                            <div class="col-md-6">
                                <label class="form-label fw-bold text-danger mb-1">Emergency Contact</label>
                                <input type="text" class="form-control border-danger" v-model="emergencyContact" placeholder="Name & Number" required />
                            </div>
                            
                            <div class="col-12 mt-4 text-center">
                                <button type="submit" class="btn btn-primary w-100 rounded-pill fw-bold py-2 shadow-sm" :disabled="isLoading">
                                    <span v-if="isLoading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                                    <span v-else>Register Now</span>
                                </button>
                            </div>
                        </form>

                        <p class="mt-4 mb-0 text-center text-muted">Already have an account? 
                            <RouterLink to="/login" class="text-primary text-decoration-none fw-bold">Log in here</RouterLink>
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