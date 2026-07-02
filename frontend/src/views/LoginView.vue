<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const email = ref('')
const password = ref('')

const router = useRouter()
const authStore = useAuthStore()

const handleLogin = async () => {
    console.log('Sending data to the backend via axios')

    try {
        const response = await axios.post('http://127.0.0.1:5000/login',{
            email: email.value,
            password: password.value
        })

        authStore.login(response.data.access_token, response.data.role)

        // Redirect the user based on their role

        if (authStore.role == 'admin'){
            router.push('/admin-dashboard')
        } else if(authStore.role == 'staff'){
            router.push('/staff-dashboard')
        } else {
            router.push('/user-dashboard')
        }
    } catch(error){
        if(error.response){
            alert(`Login Failed: ${error.response.data.msg}`)
        } else {
            console.log("Connection error: ", error)
            alert("Could not connect to the server. Is Flask Running ?")
        }
    }
}
</script>

<template>
    <div class="login-wrapper">
        <div class="login-card">
            <h2 class="text-centre mb-4" style="text-align: center;">Tma System Login</h2>
            <form @submit.prevent="handleLogin">
                <div class="mb-3">
                    <label class="form-label">Email: </label>
                    <input type="email" class="form-control" v-model="email" placeholder="amit01@gmail.com" required />
                </div>
                <div class="mb-4">
                    <label class="form-label">Password: </label>
                    <input type="password" class="form-control" v-model="password" placeholder="Enter your account password" required />
                </div>
                <button type="submit" class="custom-btn w-100">Login</button>
            </form>
        </div>
    </div>
</template>

<style scoped>
/* The 'scoped' keyword above is magic in Vue. 
  It means this CSS will ONLY affect the Login page and won't accidentally leak and break other pages!
*/

/* "How did you center the login box?"  */
.login-wrapper{
    height: 100vh; /*takes up 100% of the Viewport Height (the whole screen) */
    display: flex; /* Flexbox is the modern way to align items */
    justify-content: center; /* Centers the card horizontally (left to right) */
    align-items: center; /* Centers the card vertically (top to bottom) */
    background-color: #f4f7f6; /* A very soft, light grey background */
}

/*  "How do you change the card size or shadow?"  */
.login-card{
    width: 400px; /* Change this number to make the card wider or thinner! */
    padding: 40px;  /* Space between the text and the edge of the card */
    background-color: white;
    border-radius: 12px; /* Round the sharp corners */
    box-shadow: 0px 8px 20px rgba(0, 0, 0, 0.1); /* Adds a soft drop-shadow for a 3D float effect */
}

/*  "How do you style the button?"  */
.custom-btn {
    background-color: #2c3e50; /* Dark slate grey/blue */
    color: white;
    padding: 12px;
    border: none;
    border-radius: 6px;
    font-weight: bold;
    transition: background-color 0.3s ease; /* Makes the color change smooth instead of instant */
}

/* "How do you change the button color when I hover over it?" */
.custom-btn:hover {
    background-color: #3498db; /* Changes to a lighter, brighter blue */
    cursor: pointer; /* Turns the mouse into a clicking finger */
}
</style>