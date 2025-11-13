// src/main.js
import { createApp } from 'vue'
import App from './App.vue'

// Styles / Bootstrap
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap'
import './style.css'

// App erstellen und mounten (ohne socket.io)
createApp(App).mount('#app')
