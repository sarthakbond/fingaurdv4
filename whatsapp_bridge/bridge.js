/**
 * FinGuard WhatsApp Direct Web Bridge
 * STRICT ISOLATION MODE: ONLY operates inside "Message yourself" chat.
 * NEVER messages external contacts or groups.
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

const BACKEND_URL = process.env.FINGUARD_URL || 'http://127.0.0.1:8000';
const CHROME_PATH = process.env.CHROME_PATH || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

console.log('---------------------------------------------------------');
console.log('🛡️  FinGuard WhatsApp Forensic Shield - Initializing...');
console.log(`📡 Backend Engine: ${BACKEND_URL}`);
console.log('🔒 Mode: STRICT SELF-CHAT ONLY ("Message Yourself")');
console.log('---------------------------------------------------------');

const client = new Client({
    authStrategy: new LocalAuth({
        dataPath: path.join(__dirname, '.wwebjs_auth')
    }),
    puppeteer: {
        executablePath: fs.existsSync(CHROME_PATH) ? CHROME_PATH : undefined,
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu'
        ]
    }
});

const BOT_START_TIME = Math.floor(Date.now() / 1000);

client.on('qr', (qr) => {
    console.log('\n=========================================================');
    console.log('📱 SCAN THIS QR CODE WITH WHATSAPP ON YOUR PHONE:');
    console.log('=========================================================\n');
    qrcode.generate(qr, { small: true });

    const qrImageUrl = `https://api.qrserver.com/v1/create-qr-code/?size=350x350&data=${encodeURIComponent(qr)}`;
    const htmlPath = path.join(__dirname, 'scan_qr.html');
    const htmlContent = `<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="15">
    <title>FinGuard WhatsApp Link QR</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .card { background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 32px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.5); max-width: 420px; }
        h1 { font-size: 20px; color: #38bdf8; margin-bottom: 8px; }
        p { color: #94a3b8; font-size: 14px; margin-bottom: 24px; }
        img { border-radius: 12px; background: white; padding: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
        .steps { text-align: left; background: #0f172a; border-radius: 8px; padding: 14px; margin-top: 20px; font-size: 13px; color: #cbd5e1; line-height: 1.6; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🛡️ Link FinGuard WhatsApp Shield</h1>
        <p>Scan this QR code with WhatsApp to connect your forensic assistant.</p>
        <img src="${qrImageUrl}" alt="WhatsApp Web QR Code" width="280" height="280">
        <div class="steps">
            <strong>On your phone:</strong><br>
            1. Open WhatsApp<br>
            2. Tap <b>Linked Devices</b> &rarr; <b>Link a Device</b><br>
            3. Point your camera at this code
        </div>
    </div>
</body>
</html>`;
    fs.writeFileSync(htmlPath, htmlContent);
});

client.on('authenticated', () => {
    console.log('✅ WhatsApp authenticated successfully!');
});

client.on('ready', () => {
    console.log('\n=========================================================');
    console.log('🚀 FINGUARD SHIELD IS ONLINE (STRICT SELF-CHAT ONLY)');
    console.log(`👤 Connected Phone: ${client.info.wid.user}`);
    console.log('=========================================================');
    console.log('💡 How to use:');
    console.log('   • Open "Message yourself" (your own contact) in WhatsApp');
    console.log('   • Send "hi" or forward any media to yourself to scan.');
    console.log('   • External contacts are 100% ignored.\n');
});

const handledMessages = new Set();

async function handleIncomingMessage(msg) {
    if (!msg || !msg.id || handledMessages.has(msg.id.id)) return;
    handledMessages.add(msg.id.id);

    if (handledMessages.size > 2000) handledMessages.clear();

    // 1. HARD TIME FILTER: Ignore historical messages from sync
    if (msg.timestamp && msg.timestamp < BOT_START_TIME) {
        return;
    }

    // 2. Ignore messages without content and without media
    if (!msg.body && !msg.hasMedia) {
        return;
    }

    // 3. Prevent bot loops: Do not respond to FinGuard's own output
    if (msg.body && (
        msg.body.startsWith('🛡️ *FinGuard') ||
        msg.body.startsWith('*Welcome to FinGuard!*') ||
        msg.body.startsWith('🔍 *FinGuard System Status*') ||
        msg.body.includes('FinGuard Forensic') ||
        msg.body.includes('SEBI Registered:')
    )) {
        return;
    }

    // 4. STRICT ISOLATION GUARD: ONLY reply inside "Message Yourself"
    const myWid = client.info && client.info.wid ? client.info.wid._serialized : '';
    const myUser = client.info && client.info.wid ? client.info.wid.user : '';
    
    // Check if the chat is exclusively with oneself
    const isToMe = msg.to === myWid || (msg.to && msg.to.includes(myUser));
    const isFromMe = msg.from === myWid || (msg.from && msg.from.includes(myUser)) || msg.fromMe;
    
    // In WhatsApp, "Message yourself" has both sender and recipient matching the user's own ID
    const isStrictSelfChat = isToMe && isFromMe;

    if (!isStrictSelfChat) {
        // Drop any message that is not in the user's private "Message yourself" chat
        return;
    }

    console.log(`\n[Self-Chat Input] Body: "${(msg.body || '').slice(0, 50)}" | Media: ${msg.hasMedia}`);

    try {
        let payload = {
            sender: myWid,
            body: msg.body || ''
        };

        if (msg.hasMedia) {
            console.log('⏳ Downloading attached media...');
            const media = await msg.downloadMedia();
            if (media && media.data) {
                payload.media_base64 = media.data;
                payload.media_mimetype = media.mimetype;
                payload.filename = media.filename || 'attachment';
            }
        }

        const response = await axios.post(`${BACKEND_URL}/api/whatsapp/bridge-message`, payload, {
            timeout: 120000
        });

        if (response.data && response.data.reply) {
            await msg.reply(response.data.reply);
            console.log('✅ Reply delivered to your "Message yourself" chat!');
        }
    } catch (err) {
        console.error('❌ Processing error:', err.message);
    }
}

client.on('message', handleIncomingMessage);
client.on('message_create', handleIncomingMessage);

// Do not auto-initialize right now; wait for user consent
