<script setup>
import { ref,onMounted, computed } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

// The Tab Manager
// We default to showing the 'stats' tab when the page first loads
const currentTab = ref('stats')

// Stats STATE
const stats = ref(null)         // Holds the data from Flask
const errorMessage = ref('')   // Holds any error message

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


// 2. ACTIONS
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

// --- NEW STAFF ACTIONS ---

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

const handleUpdateTrek = async (trek) => {
    // For raw testing, we will just prompt for Name and Difficulty.
    // Remember: Your backend blocks updating dates/location if bookings exist!
    const newName = prompt("Update Trek Name:", trek.name)
    if (newName === null) return; 

    const newDifficulty = prompt("Update Difficulty (Easy/Moderate/Hard):", trek.difficulty)
    if (newDifficulty === null) return;

    try {
        const response = await axios.put(`http://127.0.0.1:5000/admin/trek/${trek.id}`, {
            name: newName,
            difficulty: newDifficulty
        }, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        alert(response.data.msg)
        fetchTreks() // Refresh the table
    } catch (error) {
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

// ==========================================
//  SMART STAFF ASSIGNMENT LOGIC
// ==========================================
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

// Automatically fetch the stats the moment this page is opened
onMounted(() => {
    fetchStats()
    fetchStaff()
    fetchTreks()
    fetchBookings()
})

const handleLogout = () => {
    authStore.logout()
    router.push('/login')
}
</script>

<template>
    <main>
        <h1>Admin Dashboard</h1>
        <p>Welcome! Your role is: {{ authStore.role }}</p>
        <button @click="handleLogout">Logout</button>

        <hr>

        <!-- THE NAVIGATION MENU -->
        <nav>
            <!-- Clicking these buttons simply changes the 'currentTab' variable -->
            <button @click="currentTab = 'stats'">Overview Stats</button>
            <button @click="currentTab = 'treks'">Manage Treks</button>
            <button @click="currentTab = 'staff'">Manage Staff</button>
            <button @click="currentTab = 'bookings'">View Bookings</button>
        </nav>

        <hr>

        <!-- THE DYNAMIC CONTENT AREAS -->
        
        <!-- Only shows up if currentTab is 'stats' -->
        <section v-if="currentTab === 'stats'">
            <h2>Statistics Overview</h2>
            <p v-if="errorMessage" style="color: red;">{{ errorMessage }}</p>

            <div v-if="stats">
                <ul>
                    <li>Total Treks: {{ stats.total_treks }}</li>
                    <li>Total Trekkers: {{ stats.total_trekkers }}</li>
                    <li>Total Staff: {{ stats.total_staffs }}</li>
                    <li>Total Bookings: {{ stats.total_bookings }}</li>
                </ul>
            </div>
            <div v-else>
                <p>Loading statistics...</p>
            </div>
        </section>

        <!-- Only shows up if currentTab is 'treks' -->
        <section v-if="currentTab === 'treks'">
            <h2>Trek Management</h2>
            
            <div style="border: 1px solid black; padding: 15px; margin-bottom: 20px;">
                <h3>Create New Trek Route</h3>
                <form @submit.prevent="handleCreateTrek">
                    <div>
                        <label>Name</label>
                        <input type="text" v-model="newTrek.name" placeholder="e.g. Everest Base Camp" required />
                    </div><br>
                    <div>
                        <label>Location</label>
                        <input type="text" v-model="newTrek.location" required />
                    </div><br>
                    <div>
                        <label>Difficulty: </label>
                        <select v-model="newTrek.difficulty">
                            <option value="Easy">Easy</option>
                            <option value="Moderate">Moderate</option>
                            <option value="Hard">Hard</option>
                        </select>
                    </div><br>
                    <div>
                        <label>Duration (Days): </label>
                        <input type="number" min="1" v-model="newTrek.duration" required />
                    </div><br>
                    <div>
                        <label>Available Slots: </label>
                        <input type="number" min="1" v-model="newTrek.available_slots" required />
                    </div><br>
                    <div>
                        <label>Start Date: </label>
                        <input type="date" v-model="newTrek.start_date" required />
                    </div><br>
                    <div>
                        <label>End Date: </label>
                        <input type="date" v-model="newTrek.end_date" required />
                    </div><br>

                    <button type="submit">Create Trek Route</button>
                </form>
            </div>

            <h3>Existing Treks</h3>
            <div style="margin-bottom: 10px;">
                <strong>Instant Filter: </strong>
                <input 
                    type="text" 
                    v-model="searchTrekQuery" 
                    placeholder="Search by Name, Staff, or Difficulty..." 
                    style="width: 300px;"
                />
                <button @click="searchTrekQuery = ''">Clear</button>
            </div>

            <table border="1" cellpadding="5">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Dates</th>
                        <th>Difficulty</th>
                        <th>Slots</th>
                        <th>Status</th>
                        <th>Assigned Staff</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="trek in filteredTreks" :key="trek.id">
                        <td>{{ trek.id }}</td>
                        <td>{{ trek.name }}<br><small>{{ trek.location }}</small></td>
                        <td>{{ trek.start_date }} to {{ trek.end_date }}<br><small>({{ trek.duration }} days)</small></td>
                        <td>{{ trek.difficulty }}</td>
                        <td>{{ trek.available_slots }}</td>
                        
                        <td :style="trek.status === 'Canceled' ? 'color: red; font-weight: bold;' : ''">
                            {{ trek.status }}
                        </td>
                        
                        <td :style="trek.assigned_staff === 'Unassigned' ? 'color: red; font-weight: bold;' : ''">
                            {{ trek.assigned_staff }}
                        </td>

                        <td>
                            <button @click="handleUpdateTrek(trek)">Update</button>
                            <button @click="openAssignmentTool(trek)">Assign Staff</button>
                            <button @click="handleEmergencyCancel(trek.id)">Cancel Trek</button>
                            <button @click="handleDeleteTrek(trek.id)">Delete</button>
                        </td>
                    </tr>
                </tbody>
            </table>

            <div v-if="activeAssignmentTrek" style="border: 2px dashed #3498db; padding: 20px; margin-top: 20px; background-color: #f8f9fa;">
                <h3>Assigning Staff to: {{ activeAssignmentTrek.name }}</h3>
                <p><strong>Trek Dates:</strong> {{ activeAssignmentTrek.start_date }} to {{ activeAssignmentTrek.end_date }}</p>

                <div v-if="availableStaffList.length === 0">
                    <p style="color: red; font-weight: bold;">
                        ⚠️ No staff members are available for these dates due to scheduling conflicts or the 10-day buffer policy.
                    </p>
                </div>

                <div v-else>
                    <label><strong>Select Available Staff: </strong></label>
                    <select v-model="selectedStaffId" style="padding: 5px; margin-right: 10px;">
                        <option disabled value="">-- Choose a Staff Member --</option>
                        
                        <option v-for="staff in availableStaffList" :key="staff.staff_id" :value="staff.staff_id">
                            {{ staff.name }} (ID: {{ staff.staff_id }})
                        </option>
                    </select>
                    
                    <button @click="submitAssignment" style="background-color: #2ecc71; color: white; padding: 5px 10px;">Confirm Assignment</button>
                </div>
                
                <br>
                <button @click="activeAssignmentTrek = null">Cancel / Close Tool</button>
            </div>
        </section>

        <!-- Only shows up if currentTab is 'staff' -->
        <section v-if="currentTab === 'staff'">
            <h2>Staff Management</h2>
            
            <div style="border: 1px solid black; padding: 15px; margin-bottom: 20px;">
                <h3>Create New Staff</h3>
                <form @submit.prevent="handleCreateStaff">
                    <div>
                        <label>Name: </label>
                        <input type="text" v-model="newStaff.name" required />
                    </div>
                    <br>
                    <div>
                        <label>Email: </label>
                        <input type="email" v-model="newStaff.email" required />
                    </div>
                    <br>
                    <div>
                        <label>Password: </label>
                        <input type="password" v-model="newStaff.password" required />
                    </div>
                    <br>
                    <div>
                        <label>Contact Details: </label>
                        <input type="text" v-model="newStaff.contact_details" required />
                    </div>
                    <br>
                    <button type="submit">Create Staff Member</button>
                </form>
            </div>

            <div style="margin-bottom: 20px; padding: 10px; background-color: #eee;">
                <strong>Search Staff: </strong>
                <input 
                    type="text" 
                    v-model="searchStaffQuery" 
                    placeholder="Search by Name or User ID..." 
                    @keyup.enter="fetchStaff"
                />
                <button @click="fetchStaff">Search</button>
                
                <button @click="searchStaffQuery = ''; fetchStaff()">Clear</button>
            </div>

            <h3>Existing Staff Members</h3>
            <table border="1" cellpadding="5">
                <thead>
                    <tr>
                        <th>Profile ID</th>
                        <th>User ID</th>
                        <th>Name</th>
                        <th>Contact</th>
                        <th>Status</th>
                        <th>Actions</th> </tr>
                </thead>
                <tbody>
                    <tr v-for="staff in staffList" :key="staff.id">
                        <td>{{ staff.id }}</td>
                        <td>{{ staff.user_id }}</td>
                        <td>{{ staff.name }}</td>
                        <td>{{ staff.contact_details }}</td> <td>{{ staff.status }}</td> <td>
                            <button @click="handleUpdateStaff(staff.user_id, staff.name, staff.contact_details)">Update</button>
                            <button @click="handleBlacklistStaff(staff.user_id)">Toggle Blacklist</button>
                            <button @click="handleDeleteStaff(staff.user_id)">Delete</button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </section>

        <!-- Only shows up if currentTab is 'bookings' -->
        <section v-if="currentTab === 'bookings'">
            <h2>All Bookings</h2>
            <button @click="fetchBookings" style="margin-bottom: 15px;">Refresh Ledger</button>

            <table border="1" cellpadding="5">
                <thead>
                    <tr>
                        <th>Booking ID</th>
                        <th>Trek Name</th>
                        <th>Start Date</th>
                        <th>Trekker Name</th>
                        <th>Trekker Email</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="booking in bookingList" :key="booking.booking_id">
                        <td>#{{ booking.booking_id }}</td>
                        <td><strong>{{ booking.trek_name }}</strong></td>
                        <td>{{ booking.trek_start_date }}</td>
                        <td>{{ booking.trekker_name }}</td>
                        <td>{{ booking.trekker_email }}</td>
                    </tr>
                </tbody>
            </table>
            <p v-if="bookingList.length === 0" style="color: gray; font-style: italic;">
                No bookings have been made on the platform yet.
            </p>
        </section>

    </main>
</template>