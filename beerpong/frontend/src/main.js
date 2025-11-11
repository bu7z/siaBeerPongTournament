// src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap'
import './style.css'
import { io } from 'socket.io-client'

// 1. Socket verbinden
const socket = io('http://localhost:5000')

// 2. App erstellen
const app = createApp(App)

// 3. Socket allen Komponenten verfügbar machen
app.provide('socket', socket)

// 4. mounten
app.mount('#app')
