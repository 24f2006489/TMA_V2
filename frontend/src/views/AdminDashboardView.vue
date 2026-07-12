<script setup>
import { ref,onMounted, computed, onUnmounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'


//-----Import Componets-------
import NeoCard from '../components/NeoCard.vue'



// --- CHART.JS IMPORTS ---
import { Bar, Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement } from 'chart.js'

// Register the chart components
ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement)

const authStore = useAuthStore()
const router = useRouter()

// The Tab Manager
// We default to showing the 'stats' tab when the page first loads
const currentTab = ref('stats')

// Stats STATE
const stats = ref(null)         // Holds the data from Flask
const errorMessage = ref('')   // Holds any error message

// --- CHART DATA GENERATORS ---
// Doughnut Chart: Compares the types of users on the platform
const userDemographicsData = computed(() => {
    if (!stats.value) return null;
    return {
        labels: ['Trekkers', 'Staff Members'],
        datasets: [{
            data: [stats.value.total_trekkers, stats.value.total_staffs],
            backgroundColor: ['rgba(54, 162, 235, 0.7)', 'rgba(255, 206, 86, 0.7)'],
            borderColor: ['#fff', '#fff'],
            borderWidth: 2
        }]
    }
})

// Bar Chart: Platform Activity
const platformActivityData = computed(() => {
    if (!stats.value) return null;
    return {
        labels: ['Active Treks', 'Total Bookings'],
        datasets: [{
            label: 'Platform Metrics',
            data: [stats.value.total_treks, stats.value.total_bookings],
            backgroundColor: ['rgba(75, 192, 192, 0.7)', 'rgba(153, 102, 255, 0.7)'],
            borderRadius: 5 // Gives the bars rounded, modern edges
        }]
    }
})

// General options to make the charts responsive and pretty
const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { position: 'bottom' }
    }
}



// ==============================
// REAL-TIME LISTENER 
// ==========================================
let sseConnection = null;
let fallbackRadar = null; // Will hold our backup polling interval

const setupRealTimeUpdates = () => {
    console.log("⏳ Tuning the radio to Flask SSE Stream...")
    sseConnection = new EventSource('http://127.0.0.1:5000/stream')

    sseConnection.onopen = () => {
        console.log("✅ SSE Radio Connected Successfully!")
    }

    // THE SHIELD: Graceful Degradation
    sseConnection.onerror = (err) => {
        console.warn("⚠️ SSE Stream interrupted. Switching to Radar Sweep (Polling Backup)...")
        
        // Shut down the broken radio to stop the infinite error loop!
        sseConnection.close() 

        // Start the Radar Sweep (Fetch new data every 3 seconds)
        if (!fallbackRadar) {
            fallbackRadar = setInterval(() => {
                // Silently refresh the critical numbers in the background
                fetchStats()
                fetchBookings()
                fetchTreks()
                fetchTrekkers()
            }, 3000)
        }
    }

    sseConnection.addEventListener('admin_dashboard_update', (event) => {
        const incomingData = JSON.parse(event.data)
        console.log("📡 INCOMING BROADCAST RECEIVED:", incomingData)

        // Visual update for slots (only runs if it was a booking event)
        if (incomingData.trek_id) {
            const trek = trekList.value.find(t => t.id === incomingData.trek_id)
            if (trek) {
                trek.available_slots = incomingData.new_available_slots
            }
        }

        setTimeout(() => {
            fetchStats()
            fetchBookings()
            fetchTrekkers()
        }, 500)
    })
}


// Staff STATE
const staffList = ref([])
const searchStaffQuery = ref('')
const newStaff = ref({
    email: '',
    password: '',
    name: '',
    contact_details: ''
})

// Trek STATE
const trekList = ref([])
const searchTrekQuery = ref('')
// Real-time Client-Side Filtering
const filteredTreks = computed(() => {
    // If the search bar is empty, just show all the treks!
    if (!searchTrekQuery.value) return trekList.value;

    const lowerCaseQuery = searchTrekQuery.value.toLowerCase();

    return trekList.value.filter(trek => {
        // Check if the query matches the name, difficulty, OR assigned staff!
        const matchName = trek.name.toLowerCase().includes(lowerCaseQuery);
        const matchDifficulty = trek.difficulty.toLowerCase().includes(lowerCaseQuery);
        const matchStaff = trek.assigned_staff.toLowerCase().includes(lowerCaseQuery);
        const matchId = trek.id.toString() === searchTrekQuery.value;

        // If ANY of these are true, keep the trek in the table!
        return matchName || matchDifficulty || matchStaff || matchId;
    });
})
const newTrek = ref({
    name: '',
    location: '',
    difficulty: 'Moderate',
    duration: 1,
    available_slots: 10,
    start_date: '',
    end_date: ''
})

// Booking STATE
const bookingList = ref([])

// Trekkers STATE
const trekkerList = ref([])
const searchTrekkerQuery = ref('')



// Monthly Report STATE
const reportList = ref([])




// ACTIONS

// Stats Action
const fetchStats = async () => {
    try{
        const response = await axios.get('http://127.0.0.1:5000/admin/dashboard/stats', {
            headers: {
                Authorization: `Bearer ${authStore.token}`
            }
        })
        stats.value = response.data
    } catch (error) {
        console.error("Failed to fetch stats:", error)
        errorMessage.value = "Failed to load dashboard statistics."
    }
}

// Staff Action
const fetchStaff = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/admin/staffs', {
            // Axios automatically turns this into /admin/staffs?search=...
            params: {
                search: searchStaffQuery.value 
            },
            headers: {
                Authorization: `Bearer ${authStore.token}`
            }
        })
        staffList.value = response.data.staff
    } catch(error) {
        console.error("Failed to fetch staff:", error)
    }
}

const handleCreateStaff = async () => {
    try {
        await axios.post('http://127.0.0.1:5000/admin/staff', newStaff.value, {
            headers: {
                Authorization: `Bearer ${authStore.token}`
            }
        })
        alert("Staff created successfully!")

        // Clear the form
        newStaff.value = { email: '', password: '', name: '', contact_details: '' }

        // Refresh the list immediately so the new staff shows up
        fetchStaff()
    } catch (error) {
        console.error("Failed to create staff:", error)
        alert("Failed to create staff. Check console.")
    }
}


const handleBlacklistStaff = async (userId) => {
    try {
        const response = await axios.put(`http://127.0.0.1:5000/admin/user/${userId}/blacklist`, {}, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        alert(response.data.msg)
        fetchStaff() // Refresh the table instantly!
    } catch (error) {
        alert(error.response?.data?.msg || "Error updating status")
    }
}

const handleDeleteStaff = async (userId) => {
    // A built-in browser confirmation popup
    if (!confirm("Are you sure you want to completely delete this staff member?")) {
        return; 
    }

    try {
        const response = await axios.delete(`http://127.0.0.1:5000/admin/staff/${userId}`, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        alert(response.data.msg)
        fetchStaff()
    } catch (error) {
        // If they have bookings, Flask will throw a 400 error which is caught here!
        alert(error.response?.data?.msg || "Error deleting staff")
    }
}

const handleUpdateStaff = async (userId, currentName, currentContact) => {
    // Using native browser prompts for quick, raw data entry
    const newName = prompt("Update Staff Name:", currentName)
    if (newName === null) return; // If they click cancel

    const newContact = prompt("Update Contact Details:", currentContact)
    if (newContact === null) return;

    try {
        const response = await axios.put(`http://127.0.0.1:5000/admin/staff/${userId}`, {
            name: newName,
            contact_details: newContact
        }, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        alert(response.data.msg)
        fetchStaff()
    } catch (error) {
        alert(error.response?.data?.msg || "Error updating staff")
    }
}

// Trek Action
const fetchTreks = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/admin/treks', {
            // Just fetch everything!
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        trekList.value = response.data.treks
    } catch (error) {
        console.error("Failed to fetch treks:", error)
    }
}

const handleCreateTrek = async () => {
    try {
        await axios.post('http://127.0.0.1:5000/admin/trek', newTrek.value, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        alert("Trek created successfully!")
        
        // Clear the form back to default values
        newTrek.value = {
            name: '', location: '', difficulty: 'Moderate', duration: 1, available_slots: 10, start_date: '', end_date: ''
        }
        
        fetchTreks() // Refresh the table
        fetchStats() // Refresh the stats tab so the "Total Treks" number goes up!
    } catch (error) {
        alert(error.response?.data?.msg || "Failed to create trek.")
    }
}


// Edit Trek Details
const isEditTrekModalOpen = ref(false)
const editingTrek = ref({
    id: null,
    name: '',
    location: '',
    difficulty: 'Moderate',
    duration: 1,
    start_date: '',
    end_date: ''
})

const openEditTrekModal = (trek) => {
    // Clone the trek data into the form so we don't accidentally mutate the table before saving
    editingTrek.value = { ...trek }
    isEditTrekModalOpen.value = true
}

const closeEditTrekModal = () => {
    isEditTrekModalOpen.value = false
}

const submitEditTrek = async () => {
    const originalTrek = trekList.value.find(t => t.id === editingTrek.value.id)

    const payload = {}
    
    if (editingTrek.value.name !== originalTrek.name) payload.name = editingTrek.value.name;
    if (editingTrek.value.difficulty !== originalTrek.difficulty) payload.difficulty = editingTrek.value.difficulty;
    
    // Explicitly handle date strings to ensure they match YYYY-MM-DD
    if (editingTrek.value.location !== originalTrek.location) payload.location = editingTrek.value.location;
    if (parseInt(editingTrek.value.duration) !== parseInt(originalTrek.duration)) payload.duration = parseInt(editingTrek.value.duration);
    
    // Ensure dates are strings in YYYY-MM-DD format
    if (editingTrek.value.start_date !== originalTrek.start_date) payload.start_date = editingTrek.value.start_date;
    if (editingTrek.value.end_date !== originalTrek.end_date) payload.end_date = editingTrek.value.end_date;

    if (Object.keys(payload).length === 0) {
        closeEditTrekModal();
        return;
    }

    try {
        // Explicitly set the headers to ensure Flask's request.get_json() recognizes the data
        const response = await axios.put(`http://127.0.0.1:5000/admin/trek/${editingTrek.value.id}`, payload, {
            headers: { 
                'Authorization': `Bearer ${authStore.token}`,
                'Content-Type': 'application/json' 
            }
        })
        alert(response.data.msg)
        fetchTreks() 
        closeEditTrekModal()
    } catch (error) {
        // This will print the actual error from Flask in your console
        console.error("Backend Error:", error.response?.data);
        alert(error.response?.data?.msg || "Error updating trek")
    }
}

const handleDeleteTrek = async (trekId) => {
    if (!confirm("Are you sure you want to completely delete this trek?")) return;

    try {
        const response = await axios.delete(`http://127.0.0.1:5000/admin/trek/${trekId}`, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        alert(response.data.msg)
        fetchTreks()
        fetchStats() // Update the dashboard stats!
    } catch (error) {
        // If users have booked this trek, Flask will block it and throw a 400 error here!
        alert(error.response?.data?.msg || "Error deleting trek")
    }
}

const handleEmergencyCancel = async (trekId) => {
    if (!confirm("🚨 EMERGENCY: Are you sure you want to cancel this trek? This will instantly free the assigned staff.")) return;

    try {
        const response = await axios.put(`http://127.0.0.1:5000/admin/trek/${trekId}/cancel`, {}, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        alert(response.data.msg)
        fetchTreks()
    } catch (error) {
        alert(error.response?.data?.msg || "Error cancelling trek")
    }
}

// =============================
// STAFF ASSIGNMENT LOGIC
// ==================  ==========
const activeAssignmentTrek = ref(null)  // Holds the trek we are currently assigning
const availableStaffList = ref([])      // Holds the filtered list from Flask
const selectedStaffId = ref('')         // Holds the ID chosen from the dropdown

const openAssignmentTool = async (trek) => {
    activeAssignmentTrek.value = trek
    selectedStaffId.value = ''      // Reset the dropdown
    availableStaffList.value = []   // Clear previous results

    try {
        const response = await axios.get('http://127.0.0.1:5000/admin/available-staff', {
            params: {
                start_date: trek.start_date,
                end_date: trek.end_date
            },
            headers: { Authorization: `Bearer ${authStore.token}`}
        })

        availableStaffList.value = response.data.staff
    } catch(error) {
        alert("Failed to fetch available staff.");
        console.error(error);
    }
}

const submitAssignment = async () => {
    if(!selectedStaffId.value) {
        alert("Please select a staff member first!");
        return;
    }
    try {
        // Send put request to lock in the assignment
        const response = await axios.put(`http://127.0.0.1:5000/admin/trek/${activeAssignmentTrek.value.id}/assign`, {
            staff_id: selectedStaffId.value
        }, {
            headers: {
                Authorization: `Bearer ${authStore.token}`
            }
        })
        alert(response.data.msg);

        // Close the console and refresh the table!
        activeAssignmentTrek.value = null; 
        fetchTreks();
    } catch (error) {
        alert(error.response?.data?.msg || "Failed to assign staff.");
    }
}

// --- BOOKINGS ACTIONS ---
const fetchBookings = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/admin/bookings', {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        bookingList.value = response.data.bookings
    } catch (error) {
        console.error("Failed to fetch bookings:", error)
    }
}


// Trekkers Action

const fetchTrekkers = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/admin/trekkers', {
            params: { search: searchTrekkerQuery.value },
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        trekkerList.value = response.data.trekkers
    } catch (error) {
        console.error("Failed to fetch trekkers:", error)
    }
}

const handleExportTrekkerHistory = async (userId) => {
    try {
        const response = await axios.post(`http://127.0.0.1:5000/admin/trekker/${userId}/export`, {}, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        // Show the success message (e.g., "CSV export has started...")
        alert(response.data.msg)
    } catch (error) {
        alert(error.response?.data?.msg || "Failed to trigger CSV export.")
    }
}


const handleToggleTrekkerStatus = async (userId) => {
    try {
        const response = await axios.put(`http://127.0.0.1:5000/admin/user/${userId}/blacklist`, {}, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        alert(response.data.msg)
        fetchTrekkers() // Refresh the table instantly
    } catch (error) {
        alert(error.response?.data?.msg || "Error updating status")
    }
}


// Monthly Report Action
const fetchReports = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/admin/reports', {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        reportList.value = response.data.reports
    } catch (error) {
        console.error("Failed to fetch reports:", error)
    }
}

// Automatically fetch the stats the moment this page is opened
onMounted(() => {
    fetchStats()
    fetchStaff()
    fetchTreks()
    fetchBookings()
    fetchTrekkers()
    fetchReports()
    setupRealTimeUpdates()
})

// Make sure we destroy the backup radar when we log out!
onUnmounted(() => {
    if (sseConnection) sseConnection.close()
    if (fallbackRadar) clearInterval(fallbackRadar) 
})

const handleLogout = () => {
    authStore.logout()
    router.push('/login')
}
</script>

<template>
    <main class="dashboard-bg p-4">
        <div class="container-fluid">
            <div class="d-flex justify-content-between align-items-center mb-4 p-3 neo-panel">
                <h2 class="mb-0 text-dark">Admin Workspace</h2>
                <div class="d-flex align-items-center gap-3">
                    <span class="badge bg-primary fs-6">Role: {{ authStore.role }}</span>
                    <button class="btn btn-outline-danger" @click="handleLogout">Logout</button>
                </div>
            </div>

            <div class="row">
                <div class="col-md-3 mb-4">
                    <div class="p-3 neo-panel">
                        <button class="nav-btn" :class="{ 'active': currentTab === 'stats'}" @click="currentTab = 'stats'">Overview Stats</button>
                        <button class="nav-btn" :class="{ 'active': currentTab === 'treks' }" @click="currentTab = 'treks'">Manage Treks</button>
                        <button class="nav-btn" :class="{ 'active': currentTab === 'staff' }" @click="currentTab = 'staff'">Manage Staff</button>
                        <button class="nav-btn" :class="{ 'active': currentTab === 'trekkers' }" @click="currentTab = 'trekkers'">Manage Trekkers</button>
                        <button class="nav-btn" :class="{ 'active': currentTab === 'bookings' }" @click="currentTab = 'bookings'">View Bookings</button>
                        <button class="nav-btn" :class="{ 'active': currentTab === 'reports' }" @click="currentTab = 'reports'">System Reports</button>
                    </div>
                </div>

                <div class="col-md-9">
                    <div class="p-4 neo-panel">
                        
                        <!-- ================= STATS TAB ================= -->
                        <section v-if="currentTab === 'stats'">
                            <h3 class="border-bottom pb-2 mb-4 text-dark">Statistics Overview</h3>
                            <p v-if="errorMessage" class="text-danger">{{ errorMessage }}</p>

                            <div v-if="stats">
                                <!-- THE SKEUO-GLASS NUMBER CARDS (using Components) -->
                                <div class="row g-4 mb-5">
                                    <div class="col-md-6 col-lg-3">
                                        <NeoCard 
                                            :value="stats.total_treks" 
                                            label="Total Treks" 
                                            textColorClass="text-primary" 
                                        />
                                    </div>
                                    <div class="col-md-6 col-lg-3">
                                        <NeoCard 
                                            :value="stats.total_trekkers" 
                                            label="Trekkers" 
                                            textColorClass="text-success" 
                                        />
                                    </div>
                                    <div class="col-md-6 col-lg-3">
                                        <NeoCard 
                                            :value="stats.total_staffs" 
                                            label="Staff Members" 
                                            textColorClass="text-warning" 
                                        />
                                    </div>
                                    <div class="col-md-6 col-lg-3">
                                        <NeoCard 
                                            :value="stats.total_bookings" 
                                            label="Total Bookings" 
                                            textColorClass="text-info" 
                                        />
                                    </div>
                                </div>

                                <!-- THE CHARTS SECTION -->
                                <h4 class="mb-3 text-secondary">Visual Analytics</h4>
                                <div class="row g-4">
                                    <!-- Doughnut Chart -->
                                    <div class="col-md-6">
                                        <div class="neo-inset">
                                            <h6 class="text-center text-muted fw-bold mb-3">User Demographics</h6>
                                            <div style="height: 250px;">
                                                <Doughnut v-if="userDemographicsData" :data="userDemographicsData" :options="chartOptions" />
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <!-- Bar Chart -->
                                    <div class="col-md-6">
                                        <div class="neo-inset">
                                            <h6 class="text-center text-muted fw-bold mb-3">Platform Activity</h6>
                                            <div style="height: 250px;">
                                                <Bar v-if="platformActivityData" :data="platformActivityData" :options="chartOptions" />
                                            </div>
                                        </div>
                                    </div>
                                </div>

                            </div>
                            <div v-else class="text-center mt-5">
                                <p class="text-muted">Loading statistics...</p>
                            </div>
                        </section>

                        <section v-if="currentTab === 'treks'">
                            <h3 class="border-bottom pb-2 mb-4">Trek Management</h3>

                            <div class="card mb-4 shadow-sm border-0 bg-light">
                                <div class="card-body">
                                    <h5 class="mb-3">Create New Trek Route</h5>
                                    <form @submit.prevent="handleCreateTrek" class="row g-3">
                                        <div class="col-md-4">
                                            <label class="form-label">Name</label>
                                            <input type="text" class="form-control" v-model="newTrek.name" required />
                                        </div>
                                        <div class="col-md-4">
                                            <label class="form-label">Location</label>
                                            <input type="text" class="form-control" v-model="newTrek.location" required />
                                        </div>
                                        <div class="col-md-4">
                                            <label class="form-label">Difficulty</label>
                                            <select class="form-select" v-model="newTrek.difficulty">
                                                <option value="Easy">Easy</option>
                                                <option value="Moderate">Moderate</option>
                                                <option value="Hard">Hard</option>
                                            </select>
                                        </div>
                                        <div class="col-md-4">
                                            <label class="form-label">Duration (Days)</label>
                                            <input type="number" min="1" class="form-control" v-model="newTrek.duration" required />
                                        </div>
                                        <div class="col-md-4">
                                            <label class="form-label">Available Slots</label>
                                            <input type="number" min="1" class="form-control" v-model="newTrek.available_slots" required />
                                        </div>
                                        <div class="col-md-2">
                                            <label class="form-label">Start Date</label>
                                            <input type="date" class="form-control" v-model="newTrek.start_date" required />
                                        </div>
                                        <div class="col-md-2">
                                            <label class="form-label">End Date</label>
                                            <input type="date" class="form-control" v-model="newTrek.end_date" required />
                                        </div>
                                        <div class="col-12 mt-3">
                                            <button type="submit" class="btn btn-primary">Create Trek Route</button>
                                        </div>
                                    </form>
                                </div>
                            </div>

                            <div class="d-flex justify-content-between align-items-center mb-3">
                                <h5 class="mb-0">Existing Treks</h5>
                                <div class="input-group w-50">
                                    <input type="text" class="form-control" v-model="searchTrekQuery" placeholder="Filter by Name, Difficulty, Staff..." />
                                    <button class="btn btn-outline-secondary" @click="searchTrekQuery = ''">Clear</button>
                                </div>
                            </div>

                            <div class="table-responsive neo-inset p-3 mb-4">
                                <table class="table table-borderless table-hover align-middle custom-table mb-0 text-nowrap">
                                    <thead class="border-bottom border-2">
                                        <tr>
                                            <th class="text-center">ID</th>
                                            <th>Name</th>
                                            <th>Dates</th>
                                            <th class="text-center">Difficulty</th>
                                            <th class="text-center">Slots</th>
                                            <th class="text-center">Status</th>
                                            <th class="text-center">Staff</th>
                                            <th class="text-center">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr v-for="trek in filteredTreks" :key="trek.id" class="border-bottom">
                                            <td class="text-center"><span class="badge bg-secondary rounded-pill px-3">{{ trek.id }}</span></td>
                                            
                                            <td><strong>{{ trek.name }}</strong><br><small class="text-muted">{{ trek.location }}</small></td>
                                            <td>{{ trek.start_date }} to {{ trek.end_date }}<br><small class="text-muted">({{ trek.duration }} days)</small></td>
                                            
                                            <td class="text-center"><span class="badge bg-dark rounded-pill">{{ trek.difficulty }}</span></td>
                                            <td class="text-center"><span class="fw-bold">{{ trek.available_slots }}</span></td>
                                            
                                            <td class="text-center">
                                                <span class="badge rounded-pill px-3"
                                                      :class="{
                                                          'bg-success': trek.status === 'Approved',
                                                          'bg-primary': trek.status === 'Open',
                                                          'bg-warning text-dark': trek.status === 'Pending',
                                                          'bg-danger': trek.status === 'Canceled',
                                                          'bg-secondary': trek.status === 'Closed' || trek.status === 'Completed'
                                                      }">
                                                    {{ trek.status }}
                                                </span>
                                            </td>
                                            
                                            <td class="text-center" :class="trek.assigned_staff === 'Unassigned' ? 'text-danger fw-bold' : 'text-primary fw-bold'">
                                                {{ trek.assigned_staff }}
                                            </td>
                                            
                                            <td class="text-center">
                                                <div class="d-flex flex-nowrap justify-content-center gap-2">
                                                    <button class="btn btn-sm btn-outline-secondary rounded-pill px-3 fw-bold" @click="openEditTrekModal(trek)">Edit</button>
                                                    <button class="btn btn-sm btn-primary rounded-pill px-3 fw-bold" @click="openAssignmentTool(trek)">Assign</button>
                                                    <button class="btn btn-sm btn-outline-warning rounded-pill px-3 fw-bold" @click="handleEmergencyCancel(trek.id)">Cancel</button>
                                                    <button class="btn btn-sm btn-outline-danger rounded-pill px-3 fw-bold" @click="handleDeleteTrek(trek.id)">Delete</button>
                                                </div>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>

                            <div v-if="activeAssignmentTrek" class="card mt-4 border-primary shadow-sm">
                                <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                                    <h5 class="mb-0">Assigning Staff to: {{ activeAssignmentTrek.name }}</h5>
                                    <button class="btn btn-sm btn-light" @click="activeAssignmentTrek = null">Close</button>
                                </div>
                                <div class="card-body">
                                    <p><strong>Trek Dates:</strong> {{ activeAssignmentTrek.start_date }} to {{ activeAssignmentTrek.end_date }}</p>
                                    <div v-if="availableStaffList.length === 0" class="alert alert-danger">
                                        ⚠️ No staff members are available for these dates due to scheduling conflicts or the 10-day buffer policy.
                                    </div>

                                    <div v-else class="d-flex align-items-center gap-3">
                                        <select class="form-select w-50" v-model="selectedStaffId">
                                            <option disabled value="">-- Choose a Staff Member --</option>
                                            <option v-for="staff in availableStaffList" :key="staff.staff_id" :value="staff.staff_id">
                                                {{ staff.name }} (ID: {{ staff.staff_id }})
                                            </option>
                                        </select>
                                        <button class="btn btn-success" @click="submitAssignment">Confirm Assignment</button>
                                    </div>
                                </div>
                            </div>
                        </section>

                        <section v-if="currentTab === 'staff'">
                            <h3 class="border-bottom pb-2 mb-4">Staff Management</h3>
                            <div class="card mb-4 shadow-sm border-0 bg-light">
                                <div class="card-body">
                                    <h5 class="mb-3">Create New Staff</h5>
                                    <form @submit.prevent="handleCreateStaff" class="row g-3">
                                        <div class="col-md-3">
                                            <label class="form-label">Name</label>
                                            <input type="text" class="form-control" v-model="newStaff.name" required />
                                        </div>
                                        <div class="col-md-3">
                                            <label class="form-label">Email</label>
                                            <input type="email" class="form-control" v-model="newStaff.email" required />
                                        </div>
                                        <div class="col-md-3">
                                            <label class="form-label">Password</label>
                                            <input type="password" class="form-control" v-model="newStaff.password" required />
                                        </div>
                                        <div class="col-md-3">
                                            <label class="form-label">Contact Details</label>
                                            <input type="text" class="form-control" v-model="newStaff.contact_details" required />
                                        </div>
                                        <div class="col-12 mt-3">
                                            <button type="submit" class="btn btn-primary">Create Staff Member</button>
                                        </div>
                                    </form>
                                </div>
                            </div>

                            <div class="d-flex justify-content-between align-items-center mb-3">
                                <h5 class="mb-0">Existing Staff Members</h5>
                                <div class="input-group w-50">
                                    <input type="text" class="form-control" v-model="searchStaffQuery" placeholder="Search by ID or Name..." @keyup.enter="fetchStaff" />
                                    <button class="btn btn-primary" @click="fetchStaff">Search</button>
                                    <button class="btn btn-outline-secondary" @click="searchStaffQuery = ''; fetchStaff()">Clear</button>
                                </div>
                            </div>

                            <!-- Wrapped in neo-inset to match the Treks table -->
                            <div class="table-responsive neo-inset p-3 mb-4">
                                <table class="table table-borderless table-hover align-middle custom-table mb-0 text-nowrap">
                                    <thead class="border-bottom border-2">
                                        <tr>
                                            <th class="text-center">User ID</th>
                                            <th>Name</th>
                                            <th>Contact</th>
                                            
                                            <!-- THE NEW SCHEDULE HEADERS -->
                                            <th class="text-center">Past Trek</th>
                                            <th class="text-center">Current Trek</th>
                                            <th class="text-center">Upcoming Trek</th>
                                            
                                            <th class="text-center">Status</th>
                                            <th class="text-center">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr v-for="staff in staffList" :key="staff.id" class="border-bottom">
                                            <td class="text-center">
                                                <span class="badge bg-secondary rounded-pill px-3">{{ staff.user_id }}</span>
                                            </td>
                                            <td><strong>{{ staff.name }}</strong></td>
                                            <td>{{ staff.contact_details }}</td>
                                            
                                            <!-- THE NEW SCHEDULE DATA CELLS -->
                                            <td class="text-center">
                                                <span :class="staff.previous_trek === 'None' ? 'text-muted fst-italic' : 'fw-bold text-secondary'">
                                                    {{ staff.previous_trek }}
                                                </span>
                                            </td>
                                            <td class="text-center">
                                                <span :class="staff.current_trek === 'None' ? 'text-muted fst-italic' : 'fw-bold text-success'">
                                                    {{ staff.current_trek }}
                                                </span>
                                            </td>
                                            <td class="text-center">
                                                <span :class="staff.upcoming_trek === 'None' ? 'text-muted fst-italic' : 'fw-bold text-primary'">
                                                    {{ staff.upcoming_trek }}
                                                </span>
                                            </td>
                                            
                                            <td class="text-center">
                                                <span class="badge rounded-pill px-3" 
                                                      :class="staff.status === 'Active' ? 'bg-success' : 'bg-danger'">
                                                    {{ staff.status }}
                                                </span>
                                            </td>
                                            <td class="text-center">
                                                <div class="d-flex flex-nowrap justify-content-center gap-2">
                                                    <button class="btn btn-sm btn-info rounded-pill px-3 fw-bold text-white" @click="router.push('/admin/staff/' + staff.user_id)">View History</button>
                                                    <button class="btn btn-sm btn-outline-secondary rounded-pill px-3 fw-bold" @click="handleUpdateStaff(staff.user_id, staff.name, staff.contact_details)">Edit</button>
                                                    <button class="btn btn-sm btn-outline-warning rounded-pill px-3 fw-bold" @click="handleBlacklistStaff(staff.user_id)">Toggle Status</button>
                                                    <button class="btn btn-sm btn-outline-danger rounded-pill px-3 fw-bold" @click="handleDeleteStaff(staff.user_id)">Delete</button>
                                                </div>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </section>


                        <section v-if="currentTab === 'trekkers'">
                            <h3 class="border-bottom pb-2 mb-4">Trekker Management</h3>

                            <div class="d-flex justify-content-between align-items-center mb-3">
                                <h5 class="mb-0">Registered Trekkers</h5>
                                <div class="input-group w-50">
                                    <input type="text" class="form-control" v-model="searchTrekkerQuery" placeholder="Search by ID or Name..." @keyup.enter="fetchTrekkers" />
                                    <button class="btn btn-primary" @click="fetchTrekkers">Search</button>
                                    <button class="btn btn-outline-secondary" @click="searchTrekkerQuery = ''; fetchTrekkers()">Clear</button>
                                </div>
                            </div>

                            <div class="table-responsive neo-inset p-3 mb-4">
                                <table class="table table-borderless table-hover align-middle custom-table mb-0 text-nowrap">
                                    <thead class="border-bottom border-2">
                                        <tr>
                                            <th class="text-center">User ID</th>
                                            <th>Trekker Info</th>
                                            <th>Emergency Contact</th>
                                            <th class="text-center">Past Trek</th>
                                            <th class="text-center">Current Trek</th>
                                            <th class="text-center">Upcoming Trek</th>
                                            <th class="text-center">Status</th>
                                            <th class="text-center">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr v-for="trekker in trekkerList" :key="trekker.user_id" class="border-bottom">
                                            <td class="text-center">
                                                <span class="badge bg-secondary rounded-pill px-3">{{ trekker.user_id }}</span>
                                            </td>
                                            
                                            <!-- Standardized Info Column -->
                                            <td>
                                                <strong>{{ trekker.name }}</strong><br>
                                                <small class="text-muted">{{ trekker.email }}</small><br>
                                                <small class="text-muted">Ph: {{ trekker.contact_details }}</small>
                                            </td>
                                            
                                            <td class="text-danger fw-bold">{{ trekker.emergency_contact }}</td>
                                            
                                            <!-- The Categorized Schedule -->
                                            <td class="text-center">
                                                <span :class="trekker.previous_trek === 'None' ? 'text-muted fst-italic' : 'fw-bold text-secondary'">
                                                    {{ trekker.previous_trek }}
                                                </span>
                                            </td>
                                            <td class="text-center">
                                                <span :class="trekker.current_trek === 'None' ? 'text-muted fst-italic' : 'fw-bold text-success'">
                                                    {{ trekker.current_trek }}
                                                </span>
                                            </td>
                                            <td class="text-center">
                                                <span :class="trekker.upcoming_trek === 'None' ? 'text-muted fst-italic' : 'fw-bold text-primary'">
                                                    {{ trekker.upcoming_trek }}
                                                </span>
                                            </td>
                                            
                                            <td class="text-center">
                                                <span class="badge rounded-pill px-3" 
                                                      :class="trekker.status === 'Active' ? 'bg-success' : 'bg-danger'">
                                                    {{ trekker.status }}
                                                </span>
                                            </td>
                                            
                                            <td class="text-center">
                                                <div class="d-flex flex-nowrap justify-content-center gap-2">
                                                    <button class="btn btn-sm btn-outline-info rounded-pill px-3 fw-bold" @click="handleExportTrekkerHistory(trekker.user_id)">Export CSV</button>
                                                    <button class="btn btn-sm btn-outline-warning rounded-pill px-3 fw-bold" @click="handleToggleTrekkerStatus(trekker.user_id)">Toggle Status</button>
                                                </div>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </section>

                        <section v-if="currentTab === 'bookings'">
                            <div class="d-flex justify-content-between align-items-center mb-4 border-bottom pb-2">
                                <h3 class="mb-0 text-dark">Global Bookings Ledger</h3>
                                <button class="btn btn-primary rounded-pill px-4 fw-bold shadow-sm" @click="fetchBookings">Refresh Ledger</button>
                            </div>

                            <div class="table-responsive neo-inset p-3 mb-4" v-if="bookingList.length > 0">
                                <table class="table table-borderless table-hover align-middle custom-table mb-0 text-nowrap">
                                    <thead class="border-bottom border-2">
                                        <tr>
                                            <th class="text-center">Receipt ID</th>
                                            <th>Trek Details</th>
                                            <th>Start Date</th>
                                            <th>Trekker Name</th>
                                            <th>Contact Email</th>
                                            <th class="text-center">Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr v-for="booking in bookingList" :key="booking.booking_id" class="border-bottom">
                                            
                                            <td class="text-center">
                                                <span class="badge bg-dark rounded-pill px-3 fs-6">#{{ booking.booking_id }}</span>
                                            </td>
                                            
                                            <td><strong>{{ booking.trek_name }}</strong></td>
                                            <td><span class="text-secondary fw-bold">{{ booking.trek_start_date }}</span></td>
                                            <td>{{ booking.trekker_name }}</td>
                                            
                                            <td>
                                                <a :href="'mailto:' + booking.trekker_email" class="text-decoration-none fw-bold">{{ booking.trekker_email }}</a>
                                            </td>

                                            <td class="text-center">
                                                <span class="badge rounded-pill px-3" 
                                                      :class="booking.status === 'Confirmed' ? 'bg-success' : 'bg-danger'">
                                                    {{ booking.status }}
                                                </span>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                            
                            <div v-else class="neo-inset text-center p-5 mb-4">
                                <h5 class="text-muted mb-0">No bookings have been made on the platform yet.</h5>
                            </div>
                        </section>


                        <section v-if="currentTab === 'reports'">
                            <div class="d-flex justify-content-between align-items-center mb-4 border-bottom pb-2">
                                <h3 class="mb-0 text-dark">System Report Archive</h3>
                                <button class="btn btn-primary rounded-pill px-4 fw-bold shadow-sm" @click="fetchReports">Refresh Archive</button>
                            </div>

                            <div class="table-responsive neo-inset p-3 mb-4" v-if="reportList.length > 0">
                                <table class="table table-borderless table-hover align-middle custom-table mb-0 text-nowrap">
                                    <thead class="border-bottom border-2">
                                        <tr>
                                            <th>Date Generated</th>
                                            <th>Report Name</th>
                                            <th>Type</th>
                                            <th class="text-center">Action</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr v-for="report in reportList" :key="report.filename" class="border-bottom">
                                            <td><span class="text-secondary fw-bold">{{ report.date_created }}</span></td>
                                            <td><strong>{{ report.filename }}</strong></td>
                                            <td><span class="badge bg-dark rounded-pill px-3">Monthly System Report</span></td>
                                            
                                            <td class="text-center">
                                                <a :href="'http://127.0.0.1:5000' + report.url" target="_blank" class="btn btn-sm btn-info text-white rounded-pill px-4 fw-bold">
                                                    📄 View / Download
                                                </a>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                            
                            <div v-else class="neo-inset text-center p-5 mb-4">
                                <h5 class="text-muted mb-0">No monthly reports have been generated yet.</h5>
                                <p class="text-muted small mt-2">Reports are generated automatically by the Celery background worker on the 1st of every month.</p>
                            </div>
                        </section>
                    </div>
                </div>
            </div>
        </div>


        <!-- ================================= -->
        <!-- EDIT Trek Modal Overlay -->
        <!-- ===================== -->
        <div v-if="isEditTrekModalOpen" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(5px); display: flex; justify-content: center; align-items: center; z-index: 1050;">
            <div class="neo-panel p-4" style="width: 90%; max-width: 700px; background: white;">
                
                <div class="d-flex justify-content-between align-items-center mb-4 border-bottom pb-2">
                    <h4 class="mb-0 text-dark fw-bold">Edit Trek Route</h4>
                    <button class="btn btn-sm btn-outline-danger fw-bold rounded-pill px-3" @click="closeEditTrekModal">Close</button>
                </div>

                <form @submit.prevent="submitEditTrek" class="row g-3">
                    <div class="col-md-6">
                        <label class="form-label fw-bold text-secondary mb-1">Trek Name</label>
                        <input type="text" class="form-control" v-model="editingTrek.name" required />
                    </div>
                    <div class="col-md-6">
                        <label class="form-label fw-bold text-secondary mb-1">Location</label>
                        <input type="text" class="form-control" v-model="editingTrek.location" required />
                    </div>
                    <div class="col-md-4">
                        <label class="form-label fw-bold text-secondary mb-1">Difficulty</label>
                        <select class="form-select" v-model="editingTrek.difficulty">
                            <option value="Easy">Easy</option>
                            <option value="Moderate">Moderate</option>
                            <option value="Hard">Hard</option>
                        </select>
                    </div>
                    <div class="col-md-4">
                        <label class="form-label fw-bold text-secondary mb-1">Start Date</label>
                        <input type="date" class="form-control" v-model="editingTrek.start_date" required />
                    </div>
                    <div class="col-md-4">
                        <label class="form-label fw-bold text-secondary mb-1">End Date</label>
                        <input type="date" class="form-control" v-model="editingTrek.end_date" required />
                    </div>
                    <div class="col-md-4 mt-3">
                        <label class="form-label fw-bold text-secondary mb-1">Duration (Days)</label>
                        <input type="number" min="1" class="form-control" v-model="editingTrek.duration" required />
                    </div>
                    
                    <div class="col-12 mt-4 text-end">
                        <button type="submit" class="btn btn-primary fw-bold px-4 py-2 rounded-pill shadow-sm">Save Changes</button>
                    </div>
                </form>

                <div class="alert alert-warning mt-4 mb-0 border-0 shadow-sm" style="font-size: 0.85rem;">
                    <strong>Security Notice:</strong> If this expedition already has active bookings, the system will strictly block any changes to its Location, Duration, or Dates to protect the trekkers' schedules. You may still correct typos in the Name or Difficulty.
                </div>

            </div>
        </div>


    </main>
</template>

<style scoped>

.dashboard-bg {
    background-color: #e9e8f7; 
    min-height: 100vh; /* Ensures the background stretches to the very bottom of the window */
}

.nav-btn {
    display: block;          /* Forces each button to drop to a new line */
    width: 100%;             /* Makes the button stretch across the entire sidebar column */
    text-align: left;        /* Aligns the text to the left side instead of centering it */
    padding: 12px 15px;      /* Adds breathing room inside the button (top/bottom, left/right) */
    margin-bottom: 8px;      /* Adds a small gap between each button */
    border: 1px solid transparent; /* Invisible border by default to prevent layout shifting later */
    background-color: transparent; /* Standard white background */
    color: #495057;          /* A soft dark gray text color */
    border-radius: 6px;      /* Slightly rounds the corners */
    transition: 0.2s ease;   /* Makes the hover color change smooth instead of instant */
    font-weight: 500;        /* Makes the text slightly bolder than normal */
}

/* When the user hovers their mouse over a sidebar button, 
change the background slightly so they know it is clickable.
*/
.nav-btn:hover {
    background-color:rgba(255, 255, 255, 0.5); 
    border-color: #dee2e6; /* Makes the border slightly visible on hover */
}
.nav-btn.active {
    background-color: #0d6efd; 
    color: white;
    border-color: #0d6efd;     
}



.custom-table {
    background-color: transparent !important;
}

.custom-table th, .custom-table td {
    background-color: transparent !important;
}


/* The Embedded Chart Container */
.neo-inset {
    background: #f4f6f9;
    border-radius: 15px;
    padding: 20px;
    
    /* By using 'inset' on the box-shadow, the physical effect is reversed.
       It looks like a tray carved INTO the screen to hold our charts. */
    box-shadow: inset 4px 4px 8px #d1d9e6, inset -4px -4px 8px #ffffff;
}

.neo-panel {
    /* A very light, semi-transparent white base */
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.7), rgba(248, 250, 252, 0.5));
    
    /* The Glassmorphism blur effect */
    backdrop-filter: blur(12px); 
    
    /* A subtle white border to simulate the edge of a glass pane */
    border: 1px solid rgba(255, 255, 255, 0.8);
    border-radius: 16px;
    
    box-shadow: 8px 8px 16px #d1d9e6, -8px -8px 16px #ffffff;
}
</style>