<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

// ---- Form fields ----
// These map 1:1 to what POST /register expects, except confirmPassword
// which is a client-side-only check and is never sent to the backend.
const name = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const contactDetails = ref('')
const emergencyContact = ref('')

const showPassword = ref(false)
const showConfirmPassword = ref(false)
const isLoading = ref(false)

const router = useRouter()

// Same fixed starfield trick as LoginView.vue — generated once, not reactive,
// so the dots don't jump to new positions on every re-render.
const stars = Array.from({ length: 45 }, () => ({
    top: `${Math.random() * 60}%`,
    left: `${Math.random() * 100}%`,
    size: `${Math.random() * 2 + 1}px`,
    delay: `${Math.random() * 4}s`,
    duration: `${Math.random() * 3 + 2}s`
}))

const handleRegister = async () => {
    // Client-side check before we even talk to the backend — the API has
    // no concept of "confirm password", so this has to be caught here.
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

        alert(response.data.msg) // "Registration successful! You can now log in."
        router.push('/login')
    } catch (error) {
        if (error.response) {
            // Backend sends 400 for missing fields, 409 if the email is taken
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
    <div class="auth-page">

        <!-- Same decorative aurora/mountain background as LoginView.vue,
             so the two pages feel like one continuous "front door" experience. -->
        <div class="aurora-bg">
            <div class="orb orb-1"></div>
            <div class="orb orb-2"></div>
            <div class="orb orb-3"></div>

            <div class="stars">
                <span v-for="(star, i) in stars" :key="i" class="star" :style="{
                    top: star.top,
                    left: star.left,
                    width: star.size,
                    height: star.size,
                    animationDelay: star.delay,
                    animationDuration: star.duration
                }"></span>
            </div>

            <div class="mountains">
                <div class="ridge ridge-back"></div>
                <div class="ridge ridge-mid"></div>
                <div class="ridge ridge-front"></div>
            </div>

            <div class="grain"></div>
        </div>

        <div class="auth-content">

            <div class="brand-pane">
                <div class="brand-mark">
                    <svg width="34" height="34" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M3 20L9 8L13 15L16 10L21 20H3Z" fill="url(#peakGrad)" stroke="white" stroke-width="0.5" stroke-linejoin="round"/>
                        <circle cx="18" cy="6" r="2" fill="#ffd27a"/>
                        <defs>
                            <linearGradient id="peakGrad" x1="3" y1="20" x2="21" y2="8" gradientUnits="userSpaceOnUse">
                                <stop stop-color="#ff8a5b"/>
                                <stop offset="1" stop-color="#8b5cf6"/>
                            </linearGradient>
                        </defs>
                    </svg>
                    <span>Trekker Basecamp</span>
                </div>

                <h1>Every trek begins<br />with a <span class="highlight">first step</span>.</h1>
                <p class="tagline">Create your basecamp account to browse expeditions, reserve your slot, and keep every booking in one place.</p>

                <ul class="feature-list">
                    <li><span class="dot"></span>Free to join, no subscription</li>
                    <li><span class="dot"></span>Instant access after registration</li>
                    <li><span class="dot"></span>Your details stay private to your account</li>
                </ul>
            </div>

            <div class="login-pane">
                <!-- Wider than the login card (440px vs 400px) purely because
                     it holds more fields — see .glass-card.wide below. -->
                <div class="glass-card wide">
                    <h2>Create your account</h2>
                    <p class="subtitle">Join Trekker Basecamp in a couple of minutes</p>

                    <form @submit.prevent="handleRegister">

                        <div class="field">
                            <label>Full Name</label>
                            <div class="input-wrap">
                                <svg class="field-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <circle cx="12" cy="8" r="3.5" stroke="currentColor" stroke-width="1.6"/>
                                    <path d="M4.5 20c1.2-3.6 4-5.5 7.5-5.5s6.3 1.9 7.5 5.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                                </svg>
                                <input type="text" v-model="name" placeholder="Your full name" required />
                            </div>
                        </div>

                        <div class="field">
                            <label>Email</label>
                            <div class="input-wrap">
                                <svg class="field-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M3 6.5L12 13L21 6.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
                                    <rect x="3" y="5" width="18" height="14" rx="2" stroke="currentColor" stroke-width="1.6"/>
                                </svg>
                                <input type="email" v-model="email" placeholder="you@example.com" required />
                            </div>
                        </div>

                        <!-- Two fields sharing one row on wider screens (see
                             .field-row below), so the form doesn't get too tall. -->
                        <div class="field-row">
                            <div class="field">
                                <label>Password</label>
                                <div class="input-wrap">
                                    <svg class="field-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <rect x="5" y="10" width="14" height="10" rx="2" stroke="currentColor" stroke-width="1.6"/>
                                        <path d="M8 10V7a4 4 0 018 0v3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                                    </svg>
                                    <input :type="showPassword ? 'text' : 'password'" v-model="password" placeholder="Create a password" required minlength="6" />
                                    <button type="button" class="toggle-visibility" @click="showPassword = !showPassword" :aria-label="showPassword ? 'Hide password' : 'Show password'">
                                        <svg v-if="!showPassword" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M1 12S5 5 12 5s11 7 11 7-4 7-11 7-11-7-11-7z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
                                            <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="1.6"/>
                                        </svg>
                                        <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M3 3L21 21" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                                            <path d="M10.6 5.2C11 5.1 11.5 5 12 5c7 0 11 7 11 7-.6 1.1-1.5 2.4-2.7 3.6M6.6 6.6C4 8.3 1 12 1 12s4 7 11 7c1.3 0 2.5-.2 3.6-.6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
                                            <path d="M9.9 9.9a3 3 0 004.2 4.2" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                                        </svg>
                                    </button>
                                </div>
                            </div>

                            <div class="field">
                                <label>Confirm Password</label>
                                <div class="input-wrap">
                                    <svg class="field-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <rect x="5" y="10" width="14" height="10" rx="2" stroke="currentColor" stroke-width="1.6"/>
                                        <path d="M8 10V7a4 4 0 018 0v3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                                    </svg>
                                    <input :type="showConfirmPassword ? 'text' : 'password'" v-model="confirmPassword" placeholder="Re-enter password" required minlength="6" />
                                    <button type="button" class="toggle-visibility" @click="showConfirmPassword = !showConfirmPassword" :aria-label="showConfirmPassword ? 'Hide password' : 'Show password'">
                                        <svg v-if="!showConfirmPassword" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M1 12S5 5 12 5s11 7 11 7-4 7-11 7-11-7-11-7z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
                                            <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="1.6"/>
                                        </svg>
                                        <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M3 3L21 21" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                                            <path d="M10.6 5.2C11 5.1 11.5 5 12 5c7 0 11 7 11 7-.6 1.1-1.5 2.4-2.7 3.6M6.6 6.6C4 8.3 1 12 1 12s4 7 11 7c1.3 0 2.5-.2 3.6-.6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
                                            <path d="M9.9 9.9a3 3 0 004.2 4.2" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                                        </svg>
                                    </button>
                                </div>
                            </div>
                        </div>

                        <div class="field">
                            <label>Contact Number</label>
                            <div class="input-wrap">
                                <svg class="field-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M5 4h3l2 5-2.5 1.5a11 11 0 005 5L14 13l5 2v3a2 2 0 01-2 2C10.5 20 4 13.5 4 6a2 2 0 011-2z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
                                </svg>
                                <input type="tel" v-model="contactDetails" placeholder="e.g. +91 98765 43210" required />
                            </div>
                        </div>

                        <div class="field">
                            <label class="emergency-label">Emergency Contact</label>
                            <div class="input-wrap emergency">
                                <svg class="field-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M12 3l8 4v5c0 5-3.4 8.4-8 9-4.6-.6-8-4-8-9V7l8-4z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
                                    <path d="M12 8v5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                                    <circle cx="12" cy="16" r="0.8" fill="currentColor"/>
                                </svg>
                                <input type="text" v-model="emergencyContact" placeholder="A contact we can reach on trail" required />
                            </div>
                            <p class="field-hint">Used only if we're unable to reach you during an expedition.</p>
                        </div>

                        <button type="submit" class="submit-btn" :disabled="isLoading">
                            <span v-if="!isLoading">Create Account</span>
                            <span v-if="!isLoading" class="arrow">→</span>
                            <span v-else class="spinner"></span>
                        </button>
                    </form>

                    <p class="footnote">Already have an account? <RouterLink to="/login">Log in here</RouterLink></p>
                </div>
            </div>

        </div>
    </div>
</template>

<style scoped>
/* ========================================
   Same visual system as LoginView.vue — see that file for a fully
   line-commented breakdown of every rule below. Only the additions
   specific to this form (.wide, .field-row, .emergency, .field-hint)
   have their own comments here.
======================================== */
.auth-page {
    position: relative;
    min-height: 100vh;
    overflow: hidden;
    background: #0e1024;
    display: flex;
    align-items: center;
    justify-content: center;
}

.aurora-bg {
    position: absolute;
    inset: 0;
    overflow: hidden;
}

.orb {
    position: absolute;
    border-radius: 50%;
    filter: blur(90px);
    opacity: 0.65;
    animation: drift 18s ease-in-out infinite;
}

.orb-1 {
    width: 520px;
    height: 520px;
    top: -120px;
    left: -100px;
    background: radial-gradient(circle at 30% 30%, #8b5cf6, transparent 70%);
    animation-duration: 22s;
}

.orb-2 {
    width: 480px;
    height: 480px;
    top: 10%;
    right: -140px;
    background: radial-gradient(circle at 60% 40%, #ff6a5b, transparent 70%);
    animation-duration: 26s;
    animation-delay: -6s;
}

.orb-3 {
    width: 420px;
    height: 420px;
    bottom: -160px;
    left: 30%;
    background: radial-gradient(circle at 50% 50%, #17c3b2, transparent 70%);
    animation-duration: 30s;
    animation-delay: -12s;
}

@keyframes drift {
    0%, 100% { transform: translate(0, 0) scale(1); }
    33% { transform: translate(40px, 30px) scale(1.08); }
    66% { transform: translate(-30px, -20px) scale(0.96); }
}

.stars {
    position: absolute;
    inset: 0;
}

.star {
    position: absolute;
    background: #ffffff;
    border-radius: 50%;
    opacity: 0.2;
    animation-name: twinkle;
    animation-iteration-count: infinite;
    animation-timing-function: ease-in-out;
}

@keyframes twinkle {
    0%, 100% { opacity: 0.15; }
    50% { opacity: 0.9; }
}

.mountains {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    height: 45vh;
}

.ridge {
    position: absolute;
    left: -5%;
    right: -5%;
    bottom: 0;
}

.ridge-back {
    height: 70%;
    background: #171a35;
    opacity: 0.75;
    clip-path: polygon(0% 60%, 10% 40%, 22% 55%, 34% 25%, 48% 50%, 60% 20%, 74% 48%, 88% 30%, 100% 55%, 100% 100%, 0% 100%);
}

.ridge-mid {
    height: 55%;
    background: #12142a;
    opacity: 0.85;
    clip-path: polygon(0% 70%, 14% 45%, 26% 65%, 40% 35%, 55% 68%, 68% 30%, 82% 60%, 94% 40%, 100% 65%, 100% 100%, 0% 100%);
}

.ridge-front {
    height: 38%;
    background: #0a0b1a;
    clip-path: polygon(0% 80%, 12% 55%, 24% 75%, 38% 50%, 50% 78%, 64% 48%, 78% 72%, 90% 55%, 100% 75%, 100% 100%, 0% 100%);
}

.grain {
    position: absolute;
    inset: 0;
    opacity: 0.05;
    mix-blend-mode: overlay;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}

.auth-content {
    position: relative;
    z-index: 2;
    width: 100%;
    max-width: 1100px;
    margin: 0 auto;
    padding: 40px 32px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    /* ^ Unlike the login page (1.1fr / 0.9fr), this is an even split —
         the register card is wider/taller than the login card, so giving
         it a bit more room keeps the two-column layout balanced. */
    gap: 60px;
    align-items: center;
}

.brand-pane {
    color: #f4f2ff;
    animation: fadeSlideUp 0.8s ease both;
}

.brand-mark {
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 700;
    letter-spacing: 0.02em;
    margin-bottom: 32px;
    opacity: 0.9;
}

.brand-pane h1 {
    font-size: 2.6rem;
    font-weight: 800;
    line-height: 1.15;
    margin-bottom: 18px;
}

.brand-pane h1 .highlight {
    background: linear-gradient(120deg, #ff8a5b, #ff5b9c 60%, #8b5cf6);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}

.tagline {
    font-size: 1.05rem;
    color: rgba(244, 242, 255, 0.7);
    line-height: 1.6;
    max-width: 440px;
    margin-bottom: 32px;
}

.feature-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 14px;
}

.feature-list li {
    display: flex;
    align-items: center;
    gap: 12px;
    color: rgba(244, 242, 255, 0.85);
    font-size: 0.95rem;
}

.feature-list .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: linear-gradient(135deg, #ff8a5b, #8b5cf6);
    flex-shrink: 0;
}

.login-pane {
    display: flex;
    justify-content: center;
    animation: fadeSlideUp 0.8s ease 0.15s both;
}

@keyframes fadeSlideUp {
    from { opacity: 0; transform: translateY(18px); }
    to { opacity: 1; transform: translateY(0); }
}

.glass-card {
    width: 100%;
    max-width: 400px;
    padding: 36px 32px;
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.07);
    border: 1px solid rgba(255, 255, 255, 0.16);
    backdrop-filter: blur(24px);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.35);
}

/* Register form has more fields than login, so it gets a bit more width
   to breathe — applied alongside .glass-card via class="glass-card wide". */
.glass-card.wide {
    max-width: 600px;
}

.glass-card h2 {
    color: #ffffff;
    font-size: 1.4rem;
    font-weight: 700;
    margin-bottom: 4px;
}

.glass-card .subtitle {
    color: rgba(255, 255, 255, 0.55);
    font-size: 0.9rem;
    margin-bottom: 28px;
}

.field {
    margin-bottom: 18px;
}

/* Puts two .field blocks (Password / Confirm Password) side by side on
   wider screens instead of stacking them, so the form doesn't get too
   tall. Collapses back to a single column on mobile — see @media below. */
.field-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
}

.field label {
    display: block;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    text-transform: uppercase;
    color: rgba(255, 255, 255, 0.5);
    margin-bottom: 8px;
}

/* Emergency Contact's label picks up the warm accent color, the same way
   it did on the Trekker Dashboard's profile form — a small visual cue
   that this field is a little more important/sensitive than the others. */
.emergency-label {
    color: rgba(255, 178, 138, 0.85) !important;
}

.input-wrap {
    position: relative;
    display: flex;
    align-items: center;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 12px;
    padding: 0 14px;
    transition: 0.2s ease;
}

.input-wrap:focus-within {
    border-color: rgba(255, 138, 91, 0.7);
    box-shadow: 0 0 0 3px rgba(255, 138, 91, 0.15);
    background: rgba(255, 255, 255, 0.09);
}

/* Emergency Contact's input pill gets a faint warm-tinted border even at
   rest (not just on focus), so it stands out slightly from the rest of
   the form without needing a completely different layout. */
.input-wrap.emergency {
    border-color: rgba(255, 138, 91, 0.35);
}

.field-icon {
    color: rgba(255, 255, 255, 0.45);
    flex-shrink: 0;
}

.input-wrap input {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    color: #ffffff;
    padding: 13px 10px;
    font-size: 0.95rem;
    min-width: 0; /* lets the input shrink properly inside the .field-row grid
                      instead of forcing its column wider than intended */
}

.input-wrap input::placeholder {
    color: rgba(255, 255, 255, 0.32);
}

.toggle-visibility {
    background: none;
    border: none;
    color: rgba(255, 255, 255, 0.45);
    cursor: pointer;
    display: flex;
    align-items: center;
    padding: 4px;
}

.toggle-visibility:hover {
    color: rgba(255, 255, 255, 0.85);
}

/* Small helper text under Emergency Contact explaining why we ask for it. */
.field-hint {
    margin-top: 6px;
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.4);
}

.submit-btn {
    width: 100%;
    margin-top: 10px;
    padding: 14px;
    border: none;
    border-radius: 12px;
    background: linear-gradient(135deg, #ff8a5b, #ff5b9c);
    color: #ffffff;
    font-weight: 700;
    font-size: 0.98rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    cursor: pointer;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    box-shadow: 0 8px 24px rgba(255, 91, 156, 0.35);
}

.submit-btn:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 12px 28px rgba(255, 91, 156, 0.45);
}

.submit-btn:disabled {
    opacity: 0.7;
    cursor: not-allowed;
}

.submit-btn .arrow {
    transition: transform 0.15s ease;
}

.submit-btn:hover:not(:disabled) .arrow {
    transform: translateX(3px);
}

.spinner {
    width: 18px;
    height: 18px;
    border: 2.5px solid rgba(255, 255, 255, 0.4);
    border-top-color: #ffffff;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.footnote {
    margin-top: 22px;
    text-align: center;
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.4);
}

/* The "Log in here" link inside .footnote — styled to match the warm
   accent gradient family used everywhere else on this page. */
.footnote :deep(a) {
    color: #ff9d6e;
    font-weight: 600;
    text-decoration: none;
}

.footnote :deep(a:hover) {
    text-decoration: underline;
}

@media (max-width: 900px) {
    .auth-content {
        grid-template-columns: 1fr;
        gap: 36px;
        padding: 32px 24px;
        text-align: center;
    }

    .brand-pane h1 {
        font-size: 2.1rem;
    }

    .tagline {
        margin-left: auto;
        margin-right: auto;
    }

    .feature-list {
        align-items: center;
    }

    .mountains {
        height: 35vh;
    }

    .login-pane {
        justify-content: center;
    }
}

@media (max-width: 560px) {
    /* Password / Confirm Password stack vertically again once the card
       itself gets narrow enough that side-by-side fields would feel cramped. */
    .field-row {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 480px) {
    .glass-card {
        padding: 28px 22px;
    }
}
</style>