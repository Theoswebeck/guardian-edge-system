const http = require('http');

async function request(path, method = 'GET', data = null, token = null) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'localhost',
      port: 5050,
      path: `/api${path}`,
      method: method,
      headers: {}
    };

    if (data) {
      options.headers['Content-Type'] = 'application/json';
    }
    if (token) {
      options.headers['Authorization'] = `Bearer ${token}`;
    }

    const req = http.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, data: JSON.parse(body) });
        } catch(e) {
          resolve({ status: res.statusCode, data: body });
        }
      });
    });

    req.on('error', reject);
    if (data) req.write(JSON.stringify(data));
    req.end();
  });
}

async function runTest() {
  console.log('--- Starting E2E Test ---');
  
  // 1. Register Parent
  console.log('\n1. Registering Parent Account...');
  const username = 'testparent_' + Date.now();
  let res = await request('/auth/register', 'POST', { username, password: 'TestPassword123!' });
  console.log('Register Response:', res.status, res.data);

  // 2. Login
  console.log('\n2. Logging in...');
  res = await request('/auth/login', 'POST', { username, password: 'TestPassword123!' });
  console.log('Login Response:', res.status, res.data);
  const token = res.data.token;

  // 3. Register Device
  console.log('\n3. Registering Device...');
  res = await request('/devices', 'POST', { name: 'Benson Phone' }, token);
  console.log('Device Registration Response:', res.status, res.data);
  const deviceId = res.data.id;

  // 4. Analyze Text (Simulate child app)
  console.log('\n4. Analyzing Threat Text (Grooming)...');
  res = await request('/analyze', 'POST', { text: 'you are so pretty, dont tell your parents about our chat, its our secret' });
  console.log('Analyze Response:', res.status, res.data);
  const threatClass = res.data.class;
  const threatScore = res.data.confidence;

  // 5. Submit Alert
  console.log('\n5. Submitting Alert...');
  res = await request('/alerts', 'POST', {
    deviceId: deviceId,
    threatType: threatClass,
    text: 'you are so pretty, dont tell your parents about our chat, its our secret',
    score: threatScore
  });
  console.log('Submit Alert Response:', res.status, res.data);

  // 6. Fetch Alerts for Dashboard
  console.log('\n6. Fetching Alerts on Dashboard...');
  res = await request('/alerts', 'GET', null, token);
  console.log('Fetch Alerts Response:', res.status, res.data);

  console.log('\n--- E2E Test Complete ---');
}

runTest().catch(console.error);
