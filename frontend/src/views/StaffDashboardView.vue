<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios';
import { useAuthStore } from '../stores/auth';
import { useRouter } from 'vue-router';

const authStore = useAuthStore()
const router = useRouter()

// Standard Tab Manager
const currentTab = ref('my-treks')

// ==========================================
// PHASE 2: PROFILE STATE & ACTIONS
// ==========================================
const userProfile = ref({
    email: '',
    name: '',
    contact_details: ''
})

const fetchProfile = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/staff/profile', {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        userProfile.value = response.data
    } catch (error) {
        console.error("Failed to load profile:", error)
    }
}

const handleUpdateProfile = async () => {
    try {
        const response = await axios.put('http://127.0.0.1:5000/staff/profile', {
            name: userProfile.value.name,
            contact_details: userProfile.value.contact_details
        }, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        alert(response.data.msg)
    } catch (error) {
        alert(error.response?.data?.msg || "Failed to update Profile.")
    }
}

// ==========================================
// COMMAND CENTER (MY TREKS)
// ==========================================
const assignedTreks = ref([])

const fetchMyTreks = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/staff/my-treks', {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        assignedTreks.value = response.data.treks
    } catch (error) {
        console.error("Failed to fetch assigned treks:", error)
    }
}

const handleStatusChange = async (trekId, newStatus) => {
    try {
        const response = await axios.put(`http://127.0.0.1:5000/staff/trek/${trekId}/status`, {
            status: newStatus
        }, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        alert(response.data.msg)
        fetchMyTreks() 
    } catch (error) {
        alert(error.response?.data?.msg || "Failed to update status")
        fetchMyTreks() 
    }
}

const handleSlotsChange = async (trekId, newSlots) => {
    if (newSlots < 0) {
        alert("Slots cannot be negative!")
        return
    }
    try {
        const response = await axios.put(`http://127.0.0.1:5000/staff/trek/${trekId}/slots`, {
            available_slots: newSlots 
        }, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        alert(response.data.msg)
        fetchMyTreks() 
    } catch (error) {
        alert(error.response?.data?.msg || "Failed to update slots")
        fetchMyTreks()
    }
}


// THE ROSTER MODAL
const isRosterModalOpen = ref(false)
const rosterData = ref(null)
const activeTrekId = ref(null) // NEW: Keeps track of WHICH trek's modal is open

const viewRoster = async (trekId) => {
    try {
        activeTrekId.value = trekId
        const response = await axios.get(`http://127.0.0.1:5000/staff/trek/${trekId}/participants`, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        rosterData.value = response.data
        isRosterModalOpen.value = true
    } catch (error) {
        alert(error.response?.data?.msg || "Failed to fetch participant roster.")
    }
}

const closeRoster = () => {
    isRosterModalOpen.value = false
    rosterData.value = null
    activeTrekId.value = null
}


// REAL-TIME STAFF ANTENNA
let sseConnection = null
let fallbackRadar = null

const setupStaffRadio = () => {
    if (sseConnection) sseConnection.close()

    sseConnection = new EventSource('http://127.0.0.1:5000/stream')
    const userId = authStore.token ? JSON.parse(atob(authStore.token.split('.')[1])).sub : ''
    
    const personalChannel = `staff_alert_${userId}`
    console.log(`📡 Tuning into staff telemetry: ${personalChannel}`)

    // Listener 1: New Bookings for this specific staff member
    sseConnection.addEventListener(personalChannel, (event) => {
        console.log("🎟️ New Booking Detected! Syncing Capacity...")
        fetchMyTreks()
        
        // If the roster modal is currently open, silently refresh it!
        if (isRosterModalOpen.value && activeTrekId.value) {
            viewRoster(activeTrekId.value)
        }
    })

    // Listener 2: Global Trekkers updating their emergency contacts
    sseConnection.addEventListener('global_roster_update', (event) => {
        console.log("📝 Participant updated profile! Syncing Roster...")
        if (isRosterModalOpen.value && activeTrekId.value) {
            // Re-fetch to pull the new contact details without closing the window
            viewRoster(activeTrekId.value)
        }
    })

    // Graceful Degradation Backup
    sseConnection.onerror = (err) => {
        console.warn("⚠️ Radio signal dropped. Switching to Radar Sweep (Polling Backup)...")
        sseConnection.close() 
        
        if (!fallbackRadar) {
            fallbackRadar = setInterval(() => {
                fetchMyTreks()
                if (isRosterModalOpen.value && activeTrekId.value) {
                    viewRoster(activeTrekId.value)
                }
            }, 3000)
        }
    }
}

const handleLogout = () => {
    authStore.logout()
    router.push('/login')
}

// Cleanup Hooks
onUnmounted(() => {
    if (sseConnection) sseConnection.close()
    if (fallbackRadar) clearInterval(fallbackRadar)
})

onMounted(() => {
    fetchProfile()
    fetchMyTreks()
    setupStaffRadio() // Start the antenna!
})
</script>

<template>
    <div class="dashboard-bg">

        <!-- HEADER BAR -->
        <header class="neo-panel topbar">
            <h1>Staff Command Center</h1>
            <div class="topbar-right">
                <span class="role-badge">{{ authStore.role }} : {{ userProfile.name }}</span>
                <button @click="handleLogout" class="btn btn-outline-danger btn-sm fw-bold">Logout</button>
            </div>
        </header>

        <!-- BODY: SIDEBAR + MAIN CONTENT (same 2-column shell as the Trekker Dashboard) -->
        <div class="dashboard-body">

            <aside class="neo-panel sidebar">
                <button
                    @click="currentTab = 'my-treks'"
                    class="nav-btn"
                    :class="{ active: currentTab === 'my-treks' }"
                >
                    My Assigned Treks
                </button>
                <button
                    @click="currentTab = 'profile'"
                    class="nav-btn"
                    :class="{ active: currentTab === 'profile' }"
                >
                    Profile Settings
                </button>
            </aside>

            <main class="neo-panel content-panel">

                <!-- ================= MY ASSIGNED TREKS ================= -->
                <section v-if="currentTab === 'my-treks'">
                    <h3 class="mb-4">Assigned Expeditions</h3>

                    <div v-if="assignedTreks.length > 0" class="embed-card">
                        <table class="staff-table">
                            <thead>
                                <tr>
                                    <th>Trek Details</th>
                                    <th>Timeline</th>
                                    <th>Capacity Info</th>
                                    <th>Manage Slots</th>
                                    <th>Manage Status</th>
                                    <th class="text-center">Roster</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="trek in assignedTreks" :key="trek.trek_id">

                                    <td>
                                        <strong>{{ trek.name }}</strong><br>
                                        <small class="text-muted-dark">{{ trek.location }} | {{ trek.difficulty }}</small>
                                    </td>

                                    <td>{{ trek.start_date }} to {{ trek.end_date }}</td>

                                    <td>
                                        Total Booked: <strong class="text-warn">{{ trek.currently_booked }}</strong><br>
                                        Original Capacity: {{ trek.total_capacity }}
                                    </td>

                                    <!-- Slot Management Control -->
                                    <td>
                                        <div class="slot-control">
                                            <input
                                                type="number"
                                                v-model.number="trek.slots_remaining"
                                                class="slot-input"
                                                min="0"
                                            >
                                            <button
                                                @click="handleSlotsChange(trek.trek_id, trek.slots_remaining)"
                                                class="btn-accent-amber"
                                            >
                                                Update
                                            </button>
                                        </div>
                                    </td>

                                    <!-- Status Management Control -->
                                    <td>
                                        <select
                                            v-model="trek.status"
                                            @change="handleStatusChange(trek.trek_id, trek.status)"
                                            class="status-select"
                                        >
                                            <option value="Approved">Approved</option>
                                            <option value="Open">Open</option>
                                            <option value="Closed">Closed</option>
                                            <option value="Completed">Completed</option>
                                        </select>
                                    </td>

                                    <!-- Roster Button -->
                                    <td class="text-center">
                                        <button
                                            @click="viewRoster(trek.trek_id)"
                                            class="btn-accent-teal"
                                        >
                                            View Participants
                                        </button>
                                    </td>

                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <div v-else class="neo-inset text-center empty-state">
                        You currently have no expeditions assigned to you.
                    </div>
                </section>

                <!-- ================= PROFILE SETTINGS ================= -->
                <section v-if="currentTab === 'profile'">
                    <h3 class="mb-4">Profile Settings</h3>

                    <div class="profile-card">
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

                            <button type="submit" class="btn-save">
                                Save Changes
                            </button>
                        </form>
                    </div>
                </section>

            </main>
        </div>

        <!-- ================= ROSTER MODAL ================= -->
        <div v-if="isRosterModalOpen && rosterData" class="modal-overlay">
            <div class="modal-card">

                <div class="modal-header">
                    <h3>{{ rosterData.trek_name }} - Roster</h3>
                    <button @click="closeRoster" class="btn btn-outline-danger btn-sm fw-bold">
                        Close
                    </button>
                </div>

                <div v-if="rosterData.participants.length > 0" class="embed-card">
                    <table class="staff-table">
                        <thead>
                            <tr>
                                <th>Booking #</th>
                                <th>Participant Name</th>
                                <th>Contact Details</th>
                                <th class="text-warn-col">Emergency Contact</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="p in rosterData.participants" :key="p.booking_id">
                                <td>#{{ p.booking_id }}</td>
                                <td class="fw-bold">{{ p.name }}</td>
                                <td>{{ p.contact_details }}</td>
                                <td class="text-warn fw-bold">{{ p.emergency_contact }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div v-else class="neo-inset text-center empty-state">
                    No trekkers have booked this expedition yet.
                </div>

            </div>
        </div>

    </div>
</template>

<style scoped>
.dashboard-bg {
    --accent: #e8a33d;        
    --accent-dark: #c8862a;   
    --accent-soft: rgba(232, 163, 61, 0.16);
    --teal: #2ec4b6;          
    --teal-dark: #229c91;     
    --panel: #f4f6fa;         
    --panel-recessed: #e7ebf1;
    --shadow-dark: #b7c2cf;   
    --shadow-light: #ffffff; 
    --text-main: #2b2f38;    
    --text-muted: #6b7280;   

    background-color: #d7dee6;  
    min-height: 100vh;
    padding: 24px;
    color: var(--text-main);
    font-family: sans-serif;
}


.neo-panel {
    background: var(--panel);
    border-radius: 16px;
    box-shadow: 8px 8px 18px var(--shadow-dark), -8px -8px 18px var(--shadow-light);
}


.topbar {
    display: flex;
    justify-content: space-between;  
    align-items: center;
    padding: 18px 26px;
    margin-bottom: 24px;
}

.topbar h1 {
    font-size: 1.5rem;
    margin: 0;
}

.topbar-right {
    display: flex;
    align-items: center;
    gap: 14px;
}

.role-badge {
    background: var(--accent-soft);  
    color: var(--accent-dark);
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: capitalize;
}

.dashboard-body {
    display: grid;
    grid-template-columns: 240px 1fr;  
    gap: 24px;
    align-items: start;
}

.sidebar {
    padding: 20px;
}

.content-panel {
    padding: 28px;
    min-height: 60vh;   
}


.nav-btn {
    display: block;
    width: 100%;
    text-align: left;
    padding: 12px 15px;
    margin-bottom: 8px;
    border: 1px solid transparent;
    background-color: transparent;
    color: var(--text-muted);
    border-radius: 8px;
    transition: 0.2s ease;
    font-weight: 500;
    cursor: pointer;
}

.nav-btn:hover {
    background-color: rgba(43, 47, 56, 0.05);  
    color: var(--text-main);
}

.nav-btn.active {
    background-color: var(--accent);
    color: #2b2f38;
    font-weight: 700;
}


.neo-inset {
    background: var(--panel-recessed);
    border-radius: 14px;
    padding: 24px;
    box-shadow: inset 5px 5px 10px var(--shadow-dark), inset -5px -5px 10px var(--shadow-light);
}

.embed-card {
    background: var(--panel-recessed);
    border-radius: 14px;
    box-shadow: inset 6px 6px 14px var(--shadow-dark), inset -6px -6px 14px var(--shadow-light);
    overflow: hidden;   
}

.empty-state {
    color: var(--text-muted);
    font-style: italic;
}

.staff-table {
    width: 100%;
    border-collapse: collapse;   
    text-align: left;
}

.staff-table thead {
    background-color: rgba(43, 47, 56, 0.04);  
    border-bottom: 1px solid rgba(43, 47, 56, 0.08);
}

.staff-table th {
    padding: 14px 16px;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: var(--text-muted);
}

.staff-table td {
    padding: 14px 16px;
    border-bottom: 1px solid rgba(43, 47, 56, 0.07);
    vertical-align: middle;
    font-size: 0.92rem;
}

.staff-table tbody tr:last-child td {
    border-bottom: none;   /* No divider line under the very last row */
}

.staff-table tbody tr:hover {
    background-color: rgba(43, 47, 56, 0.035);
}

.text-muted-dark {
    color: var(--text-muted);
}

.text-warn {
    color: var(--warn);
}

.text-warn-col {
    color: var(--warn) !important;
}

/* ========================================
   SLOT MANAGEMENT CONTROL (number input + Update button)
======================================== */
.slot-control {
    display: flex;
    align-items: center;
    gap: 8px;
}

.slot-input {
    width: 64px;
    padding: 7px 8px;
    background: var(--panel);
    border: 1px solid rgba(43, 47, 56, 0.14);
    border-radius: 8px;
    color: var(--text-main);
    text-align: center;
}

.slot-input:focus {
    outline: none;
    border-color: var(--accent); 
    box-shadow: 0 0 0 3px var(--accent-soft); 
}

/* ========================================
   STATUS DROPDOWN
======================================== */
.status-select {
    padding: 7px 10px;
    width: 120px;
    background: var(--panel);
    border: 1px solid rgba(43, 47, 56, 0.14);
    border-radius: 8px;
    color: var(--text-main);
    cursor: pointer;
}

.status-select:focus {
    outline: none;
    border-color: var(--accent);
}

/* ========================================
   ACCENT BUTTONS
======================================== */
.btn-accent-amber {
    background: var(--accent);
    color: #2b2f38;             
    border: none;
    padding: 7px 14px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 0.85rem;
    cursor: pointer;
    transition: 0.15s ease;
}

.btn-accent-amber:hover {
    background: var(--accent-dark);
}

.btn-accent-teal {
    background: var(--teal);
    color: #0d2b28;             
    border: none;
    padding: 8px 14px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 0.85rem;
    cursor: pointer;
    transition: 0.15s ease;
}

.btn-accent-teal:hover {
    background: var(--teal-dark);
}

/* ===================
   PROFILE FORM
======================================== */
.profile-card {
    background: var(--panel);
    border-radius: 14px;
    box-shadow: 6px 6px 14px var(--shadow-dark), -6px -6px 14px var(--shadow-light);
    padding: 26px;
    max-width: 480px;
}

.form-group {
    margin-bottom: 16px;
}

.form-group label {
    display: block;
    font-weight: 600;
    margin-bottom: 6px;
    font-size: 0.85rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.02em;
}

.form-input {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid rgba(43, 47, 56, 0.14);
    border-radius: 8px;
    background: var(--panel-recessed);
    color: var(--text-main);
    font-size: 0.95rem;
    transition: 0.2s ease;
}

.form-input:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-soft);
}

.form-input:disabled {
    color: var(--text-muted);
    opacity: 0.6;
}

.btn-save {
    background: var(--accent);
    color: #2b2f38;
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

/* ======================
   ROSTER MODAL
======================*/
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(20, 24, 30, 0.55);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.modal-card {
    background: var(--panel);
    border-radius: 16px;
    box-shadow: 0 24px 60px rgba(60, 72, 90, 0.28);
    padding: 26px;
    width: 90%;
    max-width: 800px;
    max-height: 80vh;
    overflow-y: auto;
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(43, 47, 56, 0.08);
    padding-bottom: 14px;
    margin-bottom: 20px;
}

.modal-header h3 {
    margin: 0;
    font-size: 1.15rem;
}

/* ===================
   RESPONSIVE
================================ */
@media (max-width: 900px) {
    .dashboard-body {
        grid-template-columns: 1fr;
    }

    .sidebar {
        display: flex;
        gap: 10px;
    }

    .nav-btn {
        margin-bottom: 0;
    }
}
</style>