import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './views/Dashboard.vue'
import ListView from './views/ListView.vue'
import Login from './views/Login.vue'
import Profile from './views/Profile.vue'
import AdminView from './views/AdminView.vue';

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/list/:id',
    name: 'ListView',
    component: ListView,
    meta: { requiresAuth: true }
  },
  {
  path: '/profile',
  name: 'Profile',
  component: Profile,
  meta: { requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: AdminView,
    meta: { requiresAuth: true }
}
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Der "Wächter" vor jedem Seitenwechsel
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token');
  const isLoggedIn = token !== null && token !== 'undefined';

  if (to.meta.requiresAuth && !isLoggedIn) {
    next('/login');
  } 
  else if (to.name === 'Login' && isLoggedIn) {
    next('/'); 
  } 
  else {
    next();
  }
})

export default router