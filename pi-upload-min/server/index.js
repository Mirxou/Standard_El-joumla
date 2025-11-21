// Minimal Express backend for Pi integration
const express = require('express')
const cors = require('cors')
const cookieParser = require('cookie-parser')
const multer = require('multer')

const app = express()
app.use(express.json())
app.use(cookieParser())
app.use(cors({
  origin: [/^http:\/\/localhost:\d+$/],
  credentials: true,
}))

// Health check
app.get('/health', (_req, res) => {
  res.json({ status: 'ok', time: new Date().toISOString() })
})

// Fake login: in production validate Pi auth result server-side
app.post('/v1/login', (req, res) => {
  const { piAccessToken, username } = req.body || {}
  if (!piAccessToken) return res.status(400).json({ error: 'Missing token' })
  // TODO: verify token with Pi Network server-side API
  res.cookie('session_id', 'dev-session-' + Date.now(), {
    httpOnly: true,
    secure: false, // set true behind HTTPS
    sameSite: 'None',
    path: '/',
  })
  res.json({ user: { username: username || 'pi-user' } })
})

// Basic chat echo endpoint
app.post('/v1/chat/default', (req, res) => {
  const { message } = req.body || {}
  if (!message) return res.status(400).json({ error: 'Empty message' })
  // Simple echo logic (replace with AI model call later)
  res.json({ reply: `Echo: ${message}` })
})

// Image upload
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 5 * 1024 * 1024 } })
app.post('/upload', upload.single('image'), (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'No file' })
  // Placeholder: store or process image
  res.json({ filename: req.file.originalname, size: req.file.size })
})

const port = process.env.PORT || 4000
app.listen(port, () => console.log(`[backend] listening on :${port}`))
