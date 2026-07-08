<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

// --- Import Component---
import TrekCard from '../components/TrekCard.vue';

const authStore = useAuthStore()
const router = useRouter()

// Standard Tab Manager
const currentTab = ref('marketplace')


//--- User STATE ----
const myBookedTrekIds = ref([])


// --- MARKETPLACE STATE ---
const availableTreks = ref([])

// Filters mapping exactly to your app.py arguments!
const searchFilters = ref({
    location: '',
    difficulty: '',
    duration: ''
})

// Ledger STATE
const myBookingsList = ref([])

// Profile STATE
const userProfile = ref({
    email: '',
    name: '',
    contact_details: '',
    emergency_contact: ''
})


// --- MARKETPLACE ACTIONS ---
const fetchMarketplace = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/treks/available', {
            params: {
                location: searchFilters.value.location,
                difficulty: searchFilters.value.difficulty,
                duration: searchFilters.value.duration
            },
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        availableTreks.value = response.data.treks
    } catch (error) {
        console.error("Failed to load marketplace:", error)
    }
}


// Fetch personal bookings on load
const fetchMyBookings = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/trekker/my-booking', {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        // Save the full list for the Ledger Table
        myBookingsList.value = response.data.bookings

        // 2. Extract active IDs to disable the "Request Booking" buttons
        myBookedTrekIds.value = response.data.bookings
            .filter(b => b.status !== 'Cancelled') 
            .map(b => b.trek_id)
    } catch (error) {
        console.error("Failed to load personal bookings", error)
    }
}

// ----- THE BOOKING ENGINE -----
const handleBooking = async (trekId) => {
    if (!confirm("Are you sure you want to book a slot for this expedition?")) return;

    try {
        const response = await axios.post('http://127.0.0.1:5000/book', { trek_id: trekId }, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        alert(response.data.msg)
        
        // 1. Instantly disable the button on the frontend!
        myBookedTrekIds.value.push(trekId)
        
        // 2. Refresh the marketplace to update slots
        fetchMarketplace()
        fetchMyBookings()
    } catch (error) {
        alert(error.response?.data?.msg || "An error occurred during booking.")
    }
}

// ----- THE CANCELLATION ENGINE -----
const handleCancelBooking = async (bookingId) => {
    if (!confirm("Are you sure you want to cancel your ticket? This action cannot be undone.")) return;

    try {
        const response = await axios.delete(`http://127.0.0.1:5000/trekker/booking/${bookingId}`, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        alert(response.data.msg)

        // Refresh the ledger to show it as "Cancelled"
        fetchMyBookings()

        // Refresh the marketplace so the slot becomes available again!
        fetchMarketplace()
    } catch (error) {
        alert(error.response?.data?.msg || "Failed to cancel booking.")
    }
}


//---- ACCOUTN AND TELMETRY ACTION----
const fetchProfile = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/trekker/profile', {
            headers: { Authorization: `Bearer ${authStore.token}`}
        })
        userProfile.value = response.data
    } catch (error) {
        console.error("Failed to load profile:", error)
    }
}

const handleUpdateProfile = async () => {
    try {
        const response = await axios.put('http://127.0.0.1:5000/trekker/profile', {
            name: userProfile.value.name,
            contact_details: userProfile.value.contact_details,
            emergency_contact: userProfile.value.emergency_contact
        }, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        alert(response.data.msg)
    } catch (error) {
        alert(error.response?.data?.msg || "Failed to update profile.")
    }
}

const handleExportHistory = async () => {
    try {
        const response = await axios.post('http://127.0.0.1:5000/trekker/export-history', {}, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        // The backend returns a 202 Accepted status indicating Celery took the job!
        alert(response.data.msg)
    } catch (error) {
        alert(error.response?.data?.msg || "Failed to trigger CSV export.")
    }
}



// =================
// TELEMETRY ARCHIVE LOGIC
// =============
const exportList = ref([])
let sseConnection = null
let fallbackRadar = null // NEW: The backup polling interval

const fetchExports = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/trekker/exports', {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        exportList.value = response.data.exports
    } catch (error) {
        console.error("Failed to fetch exports:", error)
    }
}

const setupPersonalRadio = () => {
    if (sseConnection) sseConnection.close()

    sseConnection = new EventSource('http://127.0.0.1:5000/stream')
    const userId = authStore.token ? JSON.parse(atob(authStore.token.split('.')[1])).sub : ''
    
    const personalChannel = `trekker_export_${userId}`
    console.log(`📡 Tuning into telemetry channel: ${personalChannel}`)

    sseConnection.addEventListener(personalChannel, (event) => {
        console.log("🚀 CSV Chef finished! Refreshing the archive table...")
        // Silently fetch the newly generated file into the table
        fetchExports() 
    })

    // Graceful Degradation (Exactly like Admin Dashboard)
    sseConnection.onerror = (err) => {
        console.warn("⚠️ Radio signal dropped. Switching to Radar Sweep (Polling Backup)...")
        
        // Shut down the broken radio 
        sseConnection.close() 
        
        // Start the Radar Sweep (Fetch new files every 3 seconds)
        if (!fallbackRadar) {
            fallbackRadar = setInterval(() => {
                fetchExports()
            }, 3000)
        }
    }
}

const handleLogout = () => {
    authStore.logout()
    router.push('/login')
}

// Ensure the radio turns off when they log out or leave the page
onUnmounted(() => {
    if (sseConnection) sseConnection.close()
})

onMounted(() => {
    fetchMyBookings()
    fetchMarketplace()
    fetchProfile()
    fetchExports()  
    setupPersonalRadio()
})

onUnmounted(() => {
    if (sseConnection) sseConnection.close()
    if (fallbackRadar) clearInterval(fallbackRadar)
})
</script>

<template>
    <main class="dashboard-bg p-4">
        <div class="container-fluid">
            <div class="d-flex justify-content-between align-items-center mb-4 p-3 neo-panel">
                <h2 class="mb-0 text-dark">Trekker Basecamp</h2>
                <div class="d-flex align-items-center gap-3">
                    <span class="fw-bold text-secondary">Welcome, Explorer!</span>
                    <button class="btn btn-outline-danger" @click="handleLogout">Logout</button>
                </div>
            </div>

            <div class="row">

                <div class="col-md-3 mb-4">
                    <div class="p-3 neo-panel">
                        <!-- We use dynamic Vue classes to apply the 'active' CSS if the tab matches -->
                        <button class="nav-btn" :class="{ 'active': currentTab === 'marketplace'}" @click="currentTab = 'marketplace'">Explore Treks</button>
                        <button class="nav-btn" :class="{ 'active': currentTab === 'ledger' }" @click="currentTab = 'ledger'">My Expeditions</button>
                        <button class="nav-btn" :class="{ 'active': currentTab === 'profile' }" @click="currentTab = 'profile'">Account Settings</button>
                    </div>
                </div>

                <div class="col-md-9">
                    <div class="p-4 neo-panel">

                        <section v-if="currentTab === 'marketplace'">
                            <h3 class="mb-4">Available Expeditions</h3>
                            
                            <div class="neo-inset d-flex flex-wrap gap-3 align-items-center mb-4">
                                <strong>Filter Treks: </strong>
                                
                                <input type="text" class="form-control w-auto" v-model="searchFilters.location" placeholder="Location..." />
                                
                                <select class="form-select w-auto" v-model="searchFilters.difficulty">
                                    <option value="">Any Difficulty</option>
                                    <option value="Easy">Easy</option>
                                    <option value="Moderate">Moderate</option>
                                    <option value="Hard">Hard</option>
                                </select>
                                
                                <input type="number" class="form-control w-auto" v-model="searchFilters.duration" placeholder="Max Days..." style="width: 120px;" />
                                
                                <button class="btn btn-primary fw-bold" @click="fetchMarketplace">Apply</button>
                                <button class="btn btn-outline-secondary fw-bold" @click="searchFilters = {location:'', difficulty:'', duration:''}; fetchMarketplace()">Clear</button>
                            </div>

                            <div v-if="availableTreks.length > 0" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px;">
                                
                                <TrekCard 
                                    v-for="trek in availableTreks" 
                                    :key="trek.id" 
                                    :trek="trek" 
                                    :isBooked="myBookedTrekIds.includes(trek.id)"
                                    @book="handleBooking"
                                />

                            </div>
                            
                            <div v-else style="padding: 20px; border: 1px solid red; color: red;">
                                No treks match your current filters, or all treks are fully booked!
                            </div>
                        </section>

                        <section v-if="currentTab === 'ledger'">
                            <h3 class="mb-4">My Expeditions Ledger</h3>

                            <div v-if="myBookingsList.length > 0" class="ledger-card">
                                <table class="ledger-table">
                                    <thead>
                                        <tr>
                                            <th>Booking ID</th>
                                            <th>Trek Details</th>
                                            <th>Timeline</th>
                                            <th>Status</th>
                                            <th>Action</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr v-for="booking in myBookingsList" :key="booking.booking_id">
                                            <td class="fw-bold text-secondary">#{{ booking.booking_id }}</td>

                                            <td>
                                                <strong>{{ booking.trek_name }}</strong><br>
                                                <small class="text-muted">{{ booking.location }}</small>
                                            </td>

                                            <td>{{ booking.start_date }} to {{ booking.end_date }}</td>

                                            <td>
                                                <span class="status-pill" :class="booking.status === 'Cancelled' ? 'status-cancelled' : 'status-confirmed'">
                                                    {{ booking.status }}
                                                </span>
                                            </td>

                                            <td>
                                                <button 
                                                    v-if="booking.status === 'Confirmed'" 
                                                    @click="handleCancelBooking(booking.booking_id)"
                                                    class="btn btn-outline-danger btn-sm fw-bold"
                                                >
                                                    Cancel Ticket
                                                </button>
                                                <span v-else class="text-muted fst-italic">N/A</span>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>

                            <div v-else class="neo-inset text-center text-secondary">
                                You have not booked any expeditions yet! Head over to the 'Explore Treks' tab to find your next adventure.
                            </div>
                        </section>


                        <section v-if="currentTab === 'profile'">
                            <h3 class="mb-4">Account Settings</h3>

                            <div class="profile-card">
                                <h5 class="mb-3 fw-bold">Update Personal Details</h5>
                                
                                <form @submit.prevent="handleUpdateProfile">
                                    <div class="form-group">
                                        <label>Account Email (Read Only)</label>
                                        <input type="text" :value="userProfile.email" disabled class="form-input" />
                                    </div>

                                    <div class="form-group">
                                        <label>Full Name</label>
                                        <input type="text" v-model="userProfile.name" required class="form-input" />
                                    </div>

                                    <div class="form-group">
                                        <label>Contact Number</label>
                                        <input type="text" v-model="userProfile.contact_details" required class="form-input" />
                                    </div>

                                    <div class="form-group form-group-emergency">
                                        <label>Emergency Contact</label>
                                        <input type="text" v-model="userProfile.emergency_contact" required class="form-input form-input-emergency" />
                                    </div>

                                    <button type="submit" class="btn-save">
                                        Save Changes
                                    </button>
                                </form>
                            </div>

                            <!-- DATA TELEMETRY ARCHIVE -->
                            <div class="archive-card">
                                <div class="d-flex justify-content-between align-items-center mb-3">
                                    <h5 class="mb-0 fw-bold">Data Telemetry Archive</h5>
                                    <button @click="handleExportHistory" class="btn btn-accent-warm btn-sm fw-bold">
                                        + Generate New CSV
                                    </button>
                                </div>
                                
                                <p class="text-secondary small">Click the button above to generate a snapshot of your entire booking history. The system will process it in the background and it will appear below.</p>

                                <!-- Dynamic Archive Table -->
                                <div v-if="exportList.length > 0" class="archive-table-wrap">
                                    <table class="archive-table">
                                        <thead>
                                            <tr>
                                                <th>Date Generated</th>
                                                <th>File Name</th>
                                                <th class="text-center">Action</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr v-for="file in exportList" :key="file.filename">
                                                <td>{{ file.date_created }}</td>
                                                <td><strong>{{ file.filename }}</strong></td>
                                                <td class="text-center">
                                                    <a :href="'http://127.0.0.1:5000' + file.url" target="_blank" class="download-btn">
                                                        Download
                                                    </a>
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                                
                                <div v-else class="neo-inset text-center text-secondary fst-italic">
                                    No telemetry exports have been generated yet.
                                </div>
                            </div>
                        </section>
                    </div>
                </div>
            </div>
        </div>
    </main>
</template>

<style scoped>
/* ========================================
    TREKKER THEME TOKENS
    A sage / forest palette — deliberately different from the Admin
    Dashboard's blue-violet theme, so the two dashboards read as
    distinct products rather than reskins of each other.
======================================== */
.dashboard-bg {
    --accent: #3f6d52;
    --accent-dark: #2f5940;
    --accent-soft: #e3ede7;
    --warn: #c1662f;
    --warn-dark: #a8541f;
    --shadow-dark: #b7c0af;
    --shadow-light: #ffffff;

    background-color: #dde4d8;
    min-height: 100vh;  /* Ensures the background color stretches all the way to the bottom 
       of the screen, even if there isn't much content on the page. */
}

/* ========================================
   NEO-PANEL (The Floating Card)
   Solid, opaque surface so it visibly separates from the desk.
======================================== */
.neo-panel {
    background: #f6f7f1;
    border: 1px solid rgba(255, 255, 255, 0.9);
    border-radius: 16px;
    box-shadow: 10px 10px 20px var(--shadow-dark), -10px -10px 20px var(--shadow-light);
}

.neo-inset {
    background: #e8ece2;
    border-radius: 15px;
    padding: 20px;
    
    /* Notice the word 'inset' here! It reverses the shadow logic above.
       Instead of casting a shadow OUTWARD, it casts it INWARD, making it look 
       like a physical tray carved directly into the plastic/glass surface. */
    box-shadow: inset 5px 5px 10px var(--shadow-dark), inset -5px -5px 10px var(--shadow-light);
}

/* ========================================
   LEDGER TABLE (My Expeditions)
   Carved INTO the panel it sits inside (inset shadow), rather than
   floating above it — this reads as "embedded", not as a separate card.
======================================== */
.ledger-card {
    background: #eef1e7;
    border-radius: 14px;
    box-shadow: inset 6px 6px 14px var(--shadow-dark), inset -6px -6px 14px var(--shadow-light);
    overflow: hidden; /* clips the table's square corners to match the rounded card */
}

.ledger-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
}

.ledger-table thead {
    background-color: rgba(255, 255, 255, 0.5);
    border-bottom: 1px solid rgba(183, 192, 175, 0.4);
}

.ledger-table th {
    padding: 14px 16px;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: #5c6b5c;
}

.ledger-table td {
    padding: 14px 16px;
    border-bottom: 1px solid rgba(183, 192, 175, 0.3);
    vertical-align: middle;
}

.ledger-table tbody tr:last-child td {
    border-bottom: none;
}

.ledger-table tbody tr:hover {
    background-color: rgba(255, 255, 255, 0.4);
}

/* Status Pills */
.status-pill {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 700;
}

.status-confirmed {
    background-color: #e3f6ea;
    color: #1f8a4c;
}

.status-cancelled {
    background-color: #fbe6e6;
    color: #c0392b;
}

/* ========================================
   ACCENT BUTTONS
   Overrides Bootstrap's default blue so primary actions pick up the
   Trekker theme's forest-green accent instead of matching Admin's blue.
======================================== */
.btn-primary {
    background-color: var(--accent);
    border-color: var(--accent);
}
.btn-primary:hover,
.btn-primary:focus {
    background-color: var(--accent-dark);
    border-color: var(--accent-dark);
}

.btn-accent-warm {
    background-color: var(--warn);
    color: #fff;
    border: none;
}
.btn-accent-warm:hover {
    background-color: var(--warn-dark);
    color: #fff;
}

/* ========================================
   PROFILE SECTION CARDS
   Elevated white cards (same language as .trek-card) rather than the
   old hard 2px borders, so Account Settings matches the rest of the app.
======================================== */
.profile-card {
    background: #ffffff;
    border-radius: 14px;
    box-shadow: 6px 6px 14px var(--shadow-dark), -6px -6px 14px var(--shadow-light);
    padding: 24px;
    max-width: 600px;
    margin-bottom: 30px;
}

.form-group {
    margin-bottom: 16px;
}

.form-group label {
    display: block;
    font-weight: 600;
    margin-bottom: 6px;
    font-size: 0.9rem;
    color: #495057;
}

.form-input {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #dde3d6;
    border-radius: 8px;
    background: #f6f7f1;
    font-size: 0.95rem;
    transition: 0.2s ease;
}

.form-input:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-soft);
}

.form-input:disabled {
    background: #eceee8;
    color: #8a8f86;
}

.form-group-emergency label {
    color: var(--warn-dark);
}

.form-input-emergency {
    border-color: var(--warn);
}

.form-input-emergency:focus {
    border-color: var(--warn);
    box-shadow: 0 0 0 3px rgba(193, 102, 47, 0.15);
}

.btn-save {
    background: var(--accent);
    color: #fff;
    border: none;
    padding: 10px 24px;
    border-radius: 8px;
    font-weight: 700;
    cursor: pointer;
    transition: 0.2s ease;
}
.btn-save:hover {
    background: var(--accent-dark);
}

/* Telemetry archive table — same embedded/inset treatment as the ledger,
   since it's a data list nested inside its own card. */
.archive-card {
    background: #ffffff;
    border-radius: 14px;
    box-shadow: 6px 6px 14px var(--shadow-dark), -6px -6px 14px var(--shadow-light);
    padding: 24px;
    max-width: 600px;
}

.archive-table-wrap {
    background: #eef1e7;
    border-radius: 12px;
    box-shadow: inset 4px 4px 8px var(--shadow-dark), inset -4px -4px 8px var(--shadow-light);
    overflow: hidden;
}

.archive-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
}

.archive-table thead {
    background-color: rgba(255, 255, 255, 0.5);
}

.archive-table th {
    padding: 10px 14px;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: #5c6b5c;
}

.archive-table td {
    padding: 10px 14px;
    font-size: 0.9rem;
    border-bottom: 1px solid rgba(183, 192, 175, 0.3);
}

.archive-table tbody tr:last-child td {
    border-bottom: none;
}

.download-btn {
    background: var(--accent);
    color: white;
    padding: 6px 14px;
    text-decoration: none;
    font-weight: 700;
    font-size: 12px;
    border-radius: 999px;
    display: inline-block;
}
.download-btn:hover {
    background: var(--accent-dark);
    color: white;
}

/* ========================================
   SIDEBAR NAVIGATION BUTTONS
======================================== */
.nav-btn {
    display: block;          /* Forces buttons to stack vertically */
    width: 100%;             /* Stretches button across the sidebar */
    text-align: left;        /* Pushes text to the left side */
    padding: 12px 15px;      /* Breathing room inside the button */
    margin-bottom: 8px;      /* Gap between buttons */
    border: 1px solid transparent; /* Invisible border to stop layout shifting */
    background-color: transparent; 
    color: #495057;          /* Soft dark gray text */
    border-radius: 6px;      /* Soft corners */
    transition: 0.2s ease;   /* Makes the hover effect smooth, not instant */
    font-weight: 500;        
}

/* When the mouse hovers over the button */
.nav-btn:hover {
    background-color: rgba(255, 255, 255, 0.6); /* Slight white highlight */
    border-color: #cdd6c6;
}

/* When the button is the currently active tab */
.nav-btn.active {
    background-color: var(--accent); /* Forest green, not Admin's blue */
    color: white;              /* White text for contrast */
    border-color: var(--accent);     
}
</style>