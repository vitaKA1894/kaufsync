import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './views/Dashboard.vue'
import ListView from './views/ListView.vue'
import Login from './views/Login.vue'
import Profile from './views/Profile.vue'
import AdminView from './views/AdminView.vue';
import PendingView from './views/PendingView.vue';
import LockedView from './views/LockedView.vue';
import ResetPassword from './views/ResetPassword.vue';

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
  },
  {
    path: '/pending',
    name: 'Pending',
    component: PendingView,
  },
  {
    path: '/locked',
    name: 'Locked',
    component: LockedView,
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: ResetPassword,
  },
  {
    path: '/join',
    name: 'JoinList',
    component: Dashboard, // Doesn't matter, will be redirected by guard
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
  const status = localStorage.getItem('status');

  if (to.name === 'JoinList') {
    const code = to.query.code;
    if (code) {
      localStorage.setItem('pending_join_code', code);
    }
    next('/login'); // Redirect to login, which will handle the join if already logged in or after logging in
    return;
  }

  if (to.meta.requiresAuth && !isLoggedIn) {
    next('/login');
  } 
  else if (to.name === 'Login' && isLoggedIn) {
    next('/'); 
  } 
  else if (to.meta.requiresAuth && status === 'pending' && to.name !== 'Pending') {
    next('/pending');
  }
  else if (to.meta.requiresAuth && status === 'locked' && to.name !== 'Locked') {
    next('/locked');
  }
  else {
    next();
  }
})

export default router