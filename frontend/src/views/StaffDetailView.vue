<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const staffId = route.params.id // Extracts the ID from the URL
const details = ref(null)
const isLoading = ref(true)

let sseConnection = null // We need a variable to hold our radio antenna

const fetchDetails = async () => {
    try {
        const response = await axios.get(`http://127.0.0.1:5000/admin/staff/${staffId}/details`, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        details.value = response.data
    } catch (error) {
        alert("Failed to load staff details.")
        router.push('/admin-dashboard')
    } finally {
        isLoading.value = false
    }
}

// ==========================================
//  Real-Time SSE Listener
// ==========================================
const setupRealTimeUpdates = () => {
    // 1. Tune the antenna to the Flask stream
    sseConnection = new EventSource('http://127.0.0.1:5000/stream')

    // 2. Listen specifically for 'admin_dashboard_update' events
    sseConnection.addEventListener('admin_dashboard_update', (event) => {
        const incomingData = JSON.parse(event.data)
        console.log("Real-Time Update Received:", incomingData)

        // 3. Search our local tables to see if the booked trek belongs to this staff member
        const updateParticipantCount = (trekList) => {
            const trek = trekList.find(t => t.trek_id === incomingData.trek_id)
            if (trek) {
                // If we find it, instantly recalculate the math!
                trek.slots_remaining = incomingData.new_available_slots
                trek.currently_booked = trek.total_capacity - incomingData.new_available_slots
            }
        }

        // Apply the update to both current and upcoming lists
        if (details.value) {
            updateParticipantCount(details.value.upcoming_treks)
            updateParticipantCount(details.value.current_treks)
        }
    })
}

onMounted(() => {
    fetchDetails()
    setupRealTimeUpdates()
})

// Always turn off the radio when leaving the page!
onUnmounted(() => {
    if (sseConnection) {
        sseConnection.close()
    }
})
</script>

<template>
    <main class="dashboard-bg p-4">
        <div class="container-fluid" v-if="!isLoading && details">
            
            <div class="d-flex justify-content-between align-items-center mb-4 p-3 neo-panel">
                <div class="d-flex align-items-center gap-3">
                    <button class="btn btn-outline-secondary rounded-pill" @click="router.push('/admin-dashboard')">← Back to Dashboard</button>
                    <h2 class="mb-0 text-dark">Staff Dossier: <strong>{{ details.staff_info.name }}</strong></h2>
                </div>
                <div class="d-flex align-items-center gap-3">
                    <span class="badge fs-6" :class="details.staff_info.status === 'Active' ? 'bg-success' : 'bg-danger'">{{ details.staff_info.status }}</span>
                    <span class="text-muted fw-bold">ID: #{{ details.staff_info.user_id }}</span>
                </div>
            </div>

            <div class="row g-4 mb-4">
                <div class="col-md-4">
                    <div class="neo-card text-center p-4 border-start border-4 border-secondary">
                        <h2 class="text-secondary display-5 fw-bold">{{ details.stats.total_completed }}</h2>
                        <p class="text-muted fw-bold mb-0">Total Completed Treks</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="neo-card text-center p-4 border-start border-4 border-success">
                        <h2 class="text-success display-5 fw-bold">{{ details.stats.currently_active }}</h2>
                        <p class="text-muted fw-bold mb-0">Currently Active Treks</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="neo-card text-center p-4 border-start border-4 border-primary">
                        <h2 class="text-primary display-5 fw-bold">{{ details.stats.total_upcoming }}</h2>
                        <p class="text-muted fw-bold mb-0">Upcoming Assignments</p>
                    </div>
                </div>
            </div>

            <div class="neo-panel p-4">
                
                <h4 class="mb-3 text-primary border-bottom pb-2">🚀 Upcoming Treks</h4>
                <div class="table-responsive neo-inset p-3 mb-5">
                    <table class="table table-borderless align-middle custom-table mb-0 text-nowrap">
                        <thead class="border-bottom border-2">
                            <tr>
                                <th>Trek Name</th>
                                <th>Timeline</th>
                                <th class="text-center">Difficulty</th>
                                <th class="text-center">Participants</th>
                                <th class="text-center">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="trek in details.upcoming_treks" :key="trek.trek_id" class="border-bottom">
                                <td><strong>{{ trek.name }}</strong><br><small class="text-muted">{{ trek.location }}</small></td>
                                <td>{{ trek.start_date }} to {{ trek.end_date }}<br><small class="text-muted">({{ trek.duration }} days)</small></td>
                                <td class="text-center"><span class="badge bg-dark rounded-pill">{{ trek.difficulty }}</span></td>
                                
                                <td class="text-center">
                                    <span class="fs-5 fw-bold text-primary">{{ trek.currently_booked }}</span>
                                    <span class="text-muted"> / {{ trek.total_capacity }}</span>
                                </td>
                                
                                <td class="text-center"><span class="badge bg-primary rounded-pill px-3">{{ trek.status }}</span></td>
                            </tr>
                            <tr v-if="details.upcoming_treks.length === 0">
                                <td colspan="5" class="text-center text-muted py-4">No upcoming treks assigned.</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <h4 class="mb-3 text-secondary border-bottom pb-2">📜 Completed History</h4>
                <div class="table-responsive neo-inset p-3">
                    <table class="table table-borderless align-middle custom-table mb-0 text-nowrap">
                        <thead class="border-bottom border-2">
                            <tr>
                                <th>Trek Name</th>
                                <th>Timeline</th>
                                <th class="text-center">Difficulty</th>
                                <th class="text-center">Participants Handled</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="trek in details.past_treks" :key="trek.trek_id" class="border-bottom">
                                <td><strong>{{ trek.name }}</strong><br><small class="text-muted">{{ trek.location }}</small></td>
                                <td>{{ trek.start_date }} to {{ trek.end_date }}<br><small class="text-muted">({{ trek.duration }} days)</small></td>
                                <td class="text-center"><span class="badge bg-dark rounded-pill">{{ trek.difficulty }}</span></td>
                                <td class="text-center">
                                    <span class="fs-5 fw-bold text-secondary">{{ trek.currently_booked }}</span>
                                </td>
                            </tr>
                            <tr v-if="details.past_treks.length === 0">
                                <td colspan="4" class="text-center text-muted py-4">No past treks recorded.</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

            </div>
        </div>
        <div v-else class="text-center mt-5">
            <h4 class="text-muted">Retrieving Staff Dossier...</h4>
        </div>
    </main>
</template>

<style scoped>
/* Importing our global dashboard styles so the theme remains consistent */
.dashboard-bg { background-color: #e9e8f7; min-height: 100vh; }
.custom-table { background-color: transparent !important; }
.custom-table th, .custom-table td { background-color: transparent !important; }
.custom-table th { font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.5px; color: #6c757d; }
.neo-card { background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(248, 250, 252, 0.7)); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.8); border-radius: 15px; box-shadow: 6px 6px 12px #d1d9e6, -6px -6px 12px #ffffff; transition: transform 0.2s ease-in-out; }
.neo-card:hover { transform: translateY(-3px); }
.neo-inset { background: #f4f6f9; border-radius: 15px; padding: 20px; box-shadow: inset 4px 4px 8px #d1d9e6, inset -4px -4px 8px #ffffff; }
.neo-panel { background: linear-gradient(135deg, rgba(255, 255, 255, 0.7), rgba(248, 250, 252, 0.5)); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.8); border-radius: 16px; box-shadow: 8px 8px 16px #d1d9e6, -8px -8px 16px #ffffff; }
</style>