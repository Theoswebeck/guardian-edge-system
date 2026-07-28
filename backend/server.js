require('dotenv').config();
require('express-async-errors');
const express = require('express');
const cors = require('cors');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const multer = require('multer');
const { CloudinaryStorage } = require('multer-storage-cloudinary');
const cloudinary = require('cloudinary').v2;
const db = require('./db');

const app = express();
const PORT = process.env.PORT || 5050;
const JWT_SECRET = process.env.JWT_SECRET || 'super_secret_child_protection_key_2026';

// Configure Cloudinary
cloudinary.config({
  cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
  api_key: process.env.CLOUDINARY_API_KEY,
  api_secret: process.env.CLOUDINARY_API_SECRET
});

const storage = new CloudinaryStorage({
  cloudinary: cloudinary,
  params: {
    folder: 'guardian_edge',
    format: async (req, file) => 'jpg', // Convert to jpg
    public_id: (req, file) => 'birth-cert-' + Date.now(),
  },
});
const upload = multer({ storage: storage });

app.use(cors());
app.use(express.json());

app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
  next();
});

function authenticateToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'Access token required' });
  jwt.verify(token, JWT_SECRET, (err, user) => {
    if (err) return res.status(403).json({ error: 'Invalid or expired token' });
    req.user = user;
    next();
  });
}

function authenticateDeviceToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];
  if (!token) {
    req.device = null;
    return next();
  }
  jwt.verify(token, JWT_SECRET, (err, decoded) => {
    if (!err && decoded && decoded.type === 'device') {
      req.device = decoded;
    }
    next();
  });
}

// --- AUTH ---
app.post('/api/auth/register', async (req, res) => {
  try {
    const { username, password } = req.body;
    if (!username || !password) return res.status(400).json({ error: 'Username and password required' });

    const existingUser = await db.getUserByUsername(username);
    if (existingUser) return res.status(400).json({ error: 'Username is already taken' });

    const passwordHash = await bcrypt.hash(password, 10);
    const newUser = await db.addUser({ username, passwordHash });

    const token = jwt.sign({ id: newUser.id, username: newUser.username, isAdmin: newUser.role === 'admin', status: newUser.status }, JWT_SECRET, { expiresIn: '7d' });
    res.status(201).json({ token, username: newUser.username, status: newUser.status });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Server error' });
  }
});

app.post('/api/auth/login', async (req, res) => {
  try {
    const { username, password } = req.body;
    if (!username || !password) return res.status(400).json({ error: 'Username and password required' });

    const user = await db.getUserByUsername(username);
    if (!user) return res.status(400).json({ error: 'Invalid username or password' });

    const validPassword = await bcrypt.compare(password, user.passwordHash);
    if (!validPassword) return res.status(400).json({ error: 'Invalid username or password' });

    const token = jwt.sign({ id: user.id, username: user.username, isAdmin: user.role === 'admin', status: user.status }, JWT_SECRET, { expiresIn: '7d' });
    res.json({ token, username: user.username, isAdmin: user.role === 'admin', status: user.status });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Server error' });
  }
});

// --- ADMIN ---
app.get('/api/admin/pending', authenticateToken, async (req, res) => {
  if (!req.user.isAdmin) return res.status(403).json({ error: 'Admin only' });
  res.json(await db.getPendingDevices());
});

app.post('/api/admin/approve/:id', authenticateToken, async (req, res) => {
  if (!req.user.isAdmin) return res.status(403).json({ error: 'Admin only' });
  if (await db.updateDeviceStatus(req.params.id, 'approved')) res.json({ success: true });
  else res.status(404).json({ error: 'Device not found' });
});

app.post('/api/admin/reject/:id', authenticateToken, async (req, res) => {
  if (!req.user.isAdmin) return res.status(403).json({ error: 'Admin only' });
  if (await db.updateDeviceStatus(req.params.id, 'rejected')) res.json({ success: true });
  else res.status(404).json({ error: 'Device not found' });
});

app.get('/api/admin/history/devices', authenticateToken, async (req, res) => {
  if (!req.user.isAdmin) return res.status(403).json({ error: 'Admin only' });
  res.json(await db.getAllDevicesHistory());
});

app.get('/api/admin/history/alerts', authenticateToken, async (req, res) => {
  if (!req.user.isAdmin) return res.status(403).json({ error: 'Admin only' });
  res.json(await db.getAllAlertsHistory());
});

app.get('/api/admin/logs', authenticateToken, async (req, res) => {
  if (!req.user.isAdmin) return res.status(403).json({ error: 'Admin only' });
  res.json(await db.getAdminLogs());
});

app.get('/api/admin/parents', authenticateToken, async (req, res) => {
  if (!req.user.isAdmin) return res.status(403).json({ error: 'Admin only' });
  const users = await db.getUsers();
  res.json(users.filter(u => u.role !== 'admin').map(u => ({
    id: u.id, username: u.username, status: u.status, registeredAt: u.id
  })));
});

app.post('/api/admin/parents/action', authenticateToken, async (req, res) => {
  if (!req.user.isAdmin) return res.status(403).json({ error: 'Admin only' });
  const { parentId, action } = req.body;
  if (!parentId || !['approve', 'reject'].includes(action)) return res.status(400).json({ error: 'Invalid' });
  const status = action === 'approve' ? 'approved' : 'rejected';
  if (await db.updateUserStatus(parentId, status)) res.json({ message: `Parent ${status}` });
  else res.status(404).json({ error: 'Not found' });
});

app.post('/api/admin/change-password', authenticateToken, async (req, res) => {
  if (!req.user.isAdmin) return res.status(403).json({ error: 'Admin only' });
  const { currentPassword, newPassword } = req.body;
  const user = await db.getUserById(req.user.id);
  if (!user) return res.status(404).json({ error: 'Not found' });
  const isMatch = await bcrypt.compare(currentPassword, user.passwordHash);
  if (!isMatch) return res.status(400).json({ error: 'Incorrect' });
  const newHash = await bcrypt.hash(newPassword, 10);
  if (await db.changeUserPassword(req.user.id, newHash)) res.json({ success: true });
  else res.status(500).json({ error: 'Failed' });
});

// --- DEVICES ---
app.post('/api/devices', authenticateToken, async (req, res) => {
  try {
    const { name, childDOB } = req.body;
    if (!name || !childDOB) return res.status(400).json({ error: 'Missing fields' });

    // Age check
    const birthDate = new Date(childDOB);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const m = today.getMonth() - birthDate.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) age--;
    if (age >= 18) return res.status(400).json({ error: 'Child must be under 18' });

    const newDevice = await db.addDevice({
      name, childDOB, birthCertificate: 'removed', parentId: req.user.id
    });
    res.status(201).json(newDevice);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Server error' });
  }
});

app.get('/api/devices', authenticateToken, async (req, res) => {
  res.json(await db.getDevicesByParentId(req.user.id));
});

app.get('/api/devices/:id/validate', async (req, res) => {
  try {
    const device = await db.getDeviceById(req.params.id);
    if (!device) return res.status(404).json({ error: 'Invalid pairing code' });
    if (device.status === 'pending') return res.status(403).json({ error: 'Pending approval' });
    if (device.status === 'rejected') return res.status(403).json({ error: 'Rejected' });
    const deviceToken = jwt.sign({ id: device.id, name: device.name, type: 'device' }, JWT_SECRET, { expiresIn: '365d' });
    res.json({ success: true, name: device.name, deviceToken });
  } catch (err) {
    res.status(500).json({ error: 'Server error' });
  }
});

app.post('/api/devices/:id/heartbeat', async (req, res) => {
  try {
    const updated = await db.updateDeviceHeartbeat(req.params.id);
    if (updated) res.json({ success: true, timestamp: new Date() });
    else res.status(404).json({ error: 'Device not found' });
  } catch (err) {
    res.status(500).json({ error: 'Server error' });
  }
});

// --- Helper: Filter out Android system notifications, downloads, APK files, carrier balance SMS ---
function isSystemOrCarrierNoise(text) {
  if (!text || typeof text !== 'string') return true;
  const lower = text.toLowerCase();
  const noisePatterns = [
    "downloading document", "downloading file", "downloading video", "downloading image", "downloading photo",
    "downloading audio", "downloading sticker", "downloading",
    ".apk", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".rar", ".mp4", ".mp3", "📄", "📁", "📷", "📹", "🎵",
    "check your balance", "dial *", "valid for 24", "valid for 7", "valid for 30", "mb valid", "gb valid",
    "data bundle", "airtime", "you have received",
    "items set to", "hd quality", "new message", "new messages", "checking for new message", "messages from"
  ];
  return noisePatterns.some(kw => lower.includes(kw));
}

// --- ALERTS ---
app.post('/api/alerts', authenticateDeviceToken, async (req, res) => {
  try {
    const { deviceId, threatType, text, score } = req.body;
    if (req.device && req.device.id !== deviceId) {
      return res.status(403).json({ error: 'Unauthorized device token' });
    }
    const device = await db.getDeviceById(deviceId);
    if (!device) return res.status(404).json({ error: 'Device not found' });

    if (isSystemOrCarrierNoise(text)) {
      return res.status(200).json({ ignored: true, reason: 'System or carrier noise filtered out' });
    }

    const existingAlert = await db.findRecentAlert(deviceId, text, 60);
    if (existingAlert) {
      return res.status(200).json(existingAlert);
    }

    const newAlert = await db.addAlert({
      deviceId, deviceName: device.name, threatType, text, score: parseFloat(score)
    });
    res.status(201).json(newAlert);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Server error' });
  }
});

app.get('/api/alerts', authenticateToken, async (req, res) => {
  const alerts = await db.getAlertsForParent(req.user.id);
  alerts.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  res.json(alerts);
});

app.post('/api/alerts/:id/resolve', authenticateToken, async (req, res) => {
  if (await db.resolveAlert(req.params.id, req.user.id)) res.json({ message: 'Resolved' });
  else res.status(404).json({ error: 'Not found' });
});

app.delete('/api/alerts/:id', authenticateToken, async (req, res) => {
  if (await db.deleteAlert(req.params.id, req.user.id)) res.json({ message: 'Deleted' });
  else res.status(404).json({ error: 'Not found' });
});

// --- INFERENCE ---
// Simple queue to prevent memory overload from concurrent Python processes
const analyzeQueue = [];
let isProcessingQueue = false;

async function processAnalyzeQueue() {
  if (isProcessingQueue || analyzeQueue.length === 0) return;
  isProcessingQueue = true;

  const { text, req, res } = analyzeQueue.shift();

  try {
    const { execFile } = require('child_process');
    const path = require('path');
    const scriptPath = path.join(__dirname, '..', 'infer.py');

    execFile('python', [scriptPath, text], (error, stdout, stderr) => {
      try {
        if (error) {
          res.status(500).json({ error: 'Inference execution failed' });
        } else {
          const lines = stdout.trim().split('\n');
          const jsonLine = lines.find(line => line.trim().startsWith('{') && line.trim().endsWith('}'));

          if (!jsonLine) {
            res.status(500).json({ error: 'No JSON output' });
          } else {
            const result = JSON.parse(jsonLine.trim());
            let riskScore = result.label === 0 ? Math.floor(result.confidence * 30) : Math.floor(30 + result.confidence * 70);

            // --- AI Override: Catch explicit words that the model misses ---
            const explicitKeywords = ["sex", "nude", "naked", "send pics", "horny", "masturbate", "porn", "sweetheart", "kiss", "visit me alone", "home alone", "send picture", "dirty secret"];
            const lowerText = text.toLowerCase();
            if (explicitKeywords.some(kw => lowerText.includes(kw))) {
              result.label = 2; // Grooming
              result.class = "Grooming";
              riskScore = Math.max(riskScore, 95); // Ensure it's very high
            }
            // ---------------------------------------------------------------

            // --- System & Carrier Noise Filter: Exclude file downloads, attachments, carrier notifications ---
            if (isSystemOrCarrierNoise(text)) {
              result.label = 0; // Safe
              result.class = "Safe";
              riskScore = 0;
            }
            // -------------------------------------------------------------------------------------------------

            let riskLevel = riskScore > 80 ? 'Critical Risk' : riskScore > 60 ? 'High Risk' : riskScore > 30 ? 'Suspicious' : 'Safe';

            result.riskScore = riskScore;
            result.riskLevel = riskLevel;
            res.json(result);
          }
        }
      } catch (err) {
        res.status(500).json({ error: 'Parser failed' });
      } finally {
        isProcessingQueue = false;
        processAnalyzeQueue(); // Trigger next in queue
      }
    });
  } catch (err) {
    res.status(500).json({ error: 'Analysis failed' });
    isProcessingQueue = false;
    processAnalyzeQueue();
  }
}

app.post('/api/analyze', authenticateDeviceToken, (req, res) => {
  const { text } = req.body;
  if (!text) return res.status(400).json({ error: 'Text required' });

  // Add to queue and attempt to process
  analyzeQueue.push({ text, req, res });
  processAnalyzeQueue();
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', time: new Date() });
});

app.use((err, req, res, next) => {
  console.error('Unhandled Server Error:', err);
  res.status(500).json({ error: 'Internal Server Error' });
});

app.listen(PORT, async () => {
  console.log(`Server running on port ${PORT}`);

  try {
    const users = await db.getUsers();
    if (!users.find(u => u.role === 'admin')) {
      const passwordHash = await bcrypt.hash('admin123', 10);
      await db.addUser({ username: 'admin', passwordHash, isAdmin: true });
      console.log('Default admin created.');
    }
  } catch (e) {
    console.error("Warning: DB not ready yet for admin check", e);
  }
});
