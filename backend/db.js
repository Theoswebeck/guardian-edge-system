const { Pool } = require('pg');

const poolConfig = {
  connectionString: process.env.DATABASE_URL,
};

// Render requires SSL, but the local Docker database doesn't support it
if (process.env.DATABASE_URL && !process.env.DATABASE_URL.includes('@db:5432') && !process.env.DATABASE_URL.includes('localhost')) {
  poolConfig.ssl = { rejectUnauthorized: false };
}

const pool = new Pool(poolConfig);

pool.on('error', (err, client) => {
  console.error('Unexpected error on idle client', err);
});

async function initDB() {
  const client = await pool.connect();
  try {
    await client.query(`
      CREATE TABLE IF NOT EXISTS users (
        id VARCHAR(255) PRIMARY KEY,
        username VARCHAR(255) UNIQUE NOT NULL,
        "passwordHash" VARCHAR(255) NOT NULL,
        status VARCHAR(50) DEFAULT 'pending',
        role VARCHAR(50) DEFAULT 'parent'
      );
      CREATE TABLE IF NOT EXISTS devices (
        id VARCHAR(255) PRIMARY KEY,
        "parentId" VARCHAR(255) REFERENCES users(id),
        name VARCHAR(255) NOT NULL,
        "childDOB" VARCHAR(255),
        "birthCertificate" TEXT,
        status VARCHAR(50) DEFAULT 'pending',
        "registeredAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
      CREATE TABLE IF NOT EXISTS alerts (
        id VARCHAR(255) PRIMARY KEY,
        "deviceId" VARCHAR(255) REFERENCES devices(id),
        "deviceName" VARCHAR(255),
        "threatType" VARCHAR(255),
        text TEXT,
        score NUMERIC,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved BOOLEAN DEFAULT FALSE
      );
      CREATE TABLE IF NOT EXISTS logs (
        id VARCHAR(255) PRIMARY KEY,
        action VARCHAR(255),
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);
    console.log("Database tables initialized.");
  } catch (err) {
    console.error("Error initializing tables:", err);
  } finally {
    client.release();
  }
}

initDB();

module.exports = {
  getUsers: async () => {
    const res = await pool.query("SELECT * FROM users");
    return res.rows;
  },
  getUserById: async (id) => {
    const res = await pool.query("SELECT * FROM users WHERE id = $1", [id]);
    return res.rows[0];
  },
  getUserByUsername: async (username) => {
    const res = await pool.query("SELECT * FROM users WHERE LOWER(username) = LOWER($1)", [username]);
    return res.rows[0];
  },
  getPendingUsers: async () => {
    const res = await pool.query("SELECT * FROM users WHERE status = 'pending'");
    return res.rows;
  },
  addUser: async (user) => {
    const id = Date.now().toString();
    const res = await pool.query(
      'INSERT INTO users (id, username, "passwordHash", status, role) VALUES ($1, $2, $3, $4, $5) RETURNING *',
      [id, user.username, user.passwordHash, 'pending', user.isAdmin ? 'admin' : 'parent']
    );
    return res.rows[0];
  },
  updateUserStatus: async (id, status) => {
    const res = await pool.query("UPDATE users SET status = $1 WHERE id = $2 RETURNING *", [status, id]);
    if (res.rowCount > 0) {
      const user = res.rows[0];
      await pool.query(
        "INSERT INTO logs (id, action, details) VALUES ($1, $2, $3)",
        [Date.now().toString(), `Parent ${status.charAt(0).toUpperCase() + status.slice(1)}`, `Admin ${status} the parent account for "${user.username}".`]
      );
      return true;
    }
    return false;
  },
  changeUserPassword: async (id, newPasswordHash) => {
    const res = await pool.query('UPDATE users SET "passwordHash" = $1 WHERE id = $2', [newPasswordHash, id]);
    if (res.rowCount > 0) {
      await pool.query(
        "INSERT INTO logs (id, action, details) VALUES ($1, $2, $3)",
        [Date.now().toString(), 'Password Changed', 'Admin changed their password.']
      );
      return true;
    }
    return false;
  },

  getDevices: async () => {
    const res = await pool.query("SELECT * FROM devices");
    return res.rows;
  },
  getDevicesByParentId: async (parentId) => {
    const res = await pool.query('SELECT * FROM devices WHERE "parentId" = $1', [parentId]);
    return res.rows;
  },
  getDeviceById: async (id) => {
    const res = await pool.query("SELECT * FROM devices WHERE id = $1", [id]);
    return res.rows[0];
  },
  getPendingDevices: async () => {
    const res = await pool.query(`
      SELECT d.id as "internalRef", d.id as "deviceId", d.name, d."childDOB", d."birthCertificate", u.username as "parentUsername"
      FROM devices d
      LEFT JOIN users u ON d."parentId" = u.id
      WHERE d.status = 'pending'
    `);
    return res.rows;
  },
  getAllDevicesHistory: async () => {
    const res = await pool.query(`
      SELECT d.id as "deviceId", d.name, d."childDOB", d."birthCertificate", d.status, d."registeredAt", u.username as "parentUsername"
      FROM devices d
      LEFT JOIN users u ON d."parentId" = u.id
    `);
    return res.rows;
  },
  addDevice: async (device) => {
    const id = Math.random().toString(36).substring(2, 10).toUpperCase();
    const res = await pool.query(
      'INSERT INTO devices (id, "parentId", name, "childDOB", "birthCertificate", status) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *',
      [id, device.parentId, device.name, device.childDOB || 'Not provided', device.birthCertificate || 'Not provided', 'pending']
    );
    return res.rows[0];
  },
  updateDeviceStatus: async (id, status) => {
    const res = await pool.query("UPDATE devices SET status = $1 WHERE id = $2 RETURNING *", [status, id]);
    if (res.rowCount > 0) {
      const device = res.rows[0];
      await pool.query(
        "INSERT INTO logs (id, action, details) VALUES ($1, $2, $3)",
        [Date.now().toString(), `Device ${status.charAt(0).toUpperCase() + status.slice(1)}`, `Admin ${status} the pairing request for device "${device.name}".`]
      );
      return true;
    }
    return false;
  },

  getAdminLogs: async () => {
    const res = await pool.query("SELECT * FROM logs ORDER BY timestamp DESC");
    return res.rows;
  },
  addAdminLog: async (log) => {
    const res = await pool.query(
      "INSERT INTO logs (id, action, details) VALUES ($1, $2, $3) RETURNING *",
      [Date.now().toString(), log.action, log.details]
    );
    return res.rows[0];
  },

  getAlerts: async () => {
    const res = await pool.query("SELECT * FROM alerts");
    return res.rows;
  },
  getAllAlertsHistory: async () => {
    const res = await pool.query(`
      SELECT a.*, d.name as "deviceName", u.username as "parentUsername"
      FROM alerts a
      LEFT JOIN devices d ON a."deviceId" = d.id
      LEFT JOIN users u ON d."parentId" = u.id
    `);
    return res.rows;
  },
  getAlertsForParent: async (parentId) => {
    const res = await pool.query(`
      SELECT a.*, d.name as "deviceName" FROM alerts a
      JOIN devices d ON a."deviceId" = d.id
      WHERE d."parentId" = $1
      ORDER BY a.timestamp DESC
    `, [parentId]);
    return res.rows;
  },
  addAlert: async (alert) => {
    const id = Date.now().toString() + Math.random().toString(36).substring(2, 5);
    const res = await pool.query(
      'INSERT INTO alerts (id, "deviceId", "deviceName", "threatType", text, score) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *',
      [id, alert.deviceId, alert.deviceName, alert.threatType, alert.text, alert.score]
    );
    return res.rows[0];
  },
  resolveAlert: async (alertId, parentId) => {
    const res = await pool.query(
      `UPDATE alerts SET resolved = TRUE
       WHERE id = $1
       AND "deviceId" IN (
         SELECT id FROM devices WHERE "parentId" = $2
       )`,
      [alertId, parentId]
    );
    return res.rowCount > 0;
  }
};
