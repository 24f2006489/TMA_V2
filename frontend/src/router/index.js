import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import LoginView from '../views/LoginView.vue'
import AdminDashboardView from '../views/AdminDashboardView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/login'
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/admin-dashboard',
      name: 'admin-dashboard',
      component: AdminDashboardView,
      meta: { requiresAuth: true, requiredRole: 'admin' }
    },
    {
      path: '/admin/staff/:id', // The :id makes this dynamic!
      name: 'staff-details',
      component: () => import('../views/StaffDetailView.vue')
    },
  ]
})

// ==========================================
//  GLOBAL ROUTE GUARD (The Frontend Bouncer)
// ==========================================
router.beforeEach((to, from) => {
  const authStore = useAuthStore()

  // Is this route protected?
  if (to.meta.requiresAuth) {
    // Is the user actually logged in?
    if (!authStore.token) {
      alert("Access Denied: You must be logged in to view this page.")
      return '/login' // <-- Modern Vue syntax (no next())
    }

    // Does the user have the correct role?
    if (to.meta.requiredRole && to.meta.requiredRole !== authStore.role) {
      alert(`Access Denied: You need ${to.meta.requiredRole} privileges.`)
      return false // <-- Modern Vue syntax to cancel navigation
    }
  }
  // If all checks pass, we don't need to return anything, it just proceeds!
})
export default router
