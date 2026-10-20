/**
 * FinGuard WhatsApp Direct Web Bridge
 * Pairs with your WhatsApp account via QR code.
 * Seamlessly analyzes messages, audio voice notes, images, videos, and APKs forwarded to yourself or received in chat.
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

let qrCodeReceived = false;

client.on('qr', (qr) => {
    qrCodeReceived = true;
    console.log('\n=========================================================');
    console.log('📱 SCAN THIS QR CODE WITH WHATSAPP ON YOUR PHONE:');
    console.log('   1. Open WhatsApp on your phone');
    console.log('   2. Tap Settings (iOS) or 3 dots (Android) -> "Linked Devices"');
    console.log('   3. Tap "Link a Device" and point your camera at this QR code:');
    console.log('=========================================================\n');
    
    // Print QR code in terminal
    qrcode.generate(qr, { small: true });

    // Also write a friendly HTML preview with QR code so user can view in browser if preferred
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
    console.log(`\n[QR Preview File Saved]: ${htmlPath}`);
});

client.on('authenticated', () => {
    console.log('✅ WhatsApp authenticated successfully! Restoring session...');
});

client.on('auth_failure', (msg) => {
    console.error('❌ Authentication failure:', msg);
});

client.on('ready', () => {
    console.log('\n=========================================================');
    console.log('🚀 FINGUARD WHATSAPP SHIELD IS ONLINE & MONITORING!');
    console.log('=========================================================');
    console.log('💡 How to use:');
    console.log('   • Open "Message yourself" in WhatsApp on your phone');
    console.log('   • Type "hi" to receive the Onboarding Shield Guide');
    console.log('   • Forward any suspicious stock tip, voice note, screenshot, or video!');
    console.log('   • FinGuard analyzes it instantly and replies in the chat.\n');
});

// Avoid infinite reply loops and duplicate handling
const handledMessages = new Set();

async function handleIncomingMessage(msg) {
    if (!msg || !msg.id || handledMessages.has(msg.id.id)) return;
    handledMessages.add(msg.id.id);

    // Clean cache if too large
    if (handledMessages.size > 2000) {
        handledMessages.clear();
    }

    // Do not respond to messages sent by FinGuard itself
    if (msg.body && (
        msg.body.startsWith('🛡️ *FinGuard') ||
        msg.body.startsWith('*Welcome to FinGuard!*') ||
        msg.body.startsWith('🔍 *FinGuard System Status*') ||
        msg.body.includes('FinGuard Forensic') ||
        msg.body.includes('SEBI Registered:')
    )) {
        return;
    }

    // Skip group messages unless mentioned
    if (msg.from && msg.from.endsWith('@g.us')) {
        const isMentioned = msg.mentionedIds && msg.mentionedIds.includes(client.info.wid._serialized);
        if (!isMentioned) return;
    }

    const myWid = client.info && client.info.wid ? client.info.wid._serialized : '';
    const isSelfChat = (msg.from === myWid && msg.to === myWid) || (msg.fromMe && msg.to === myWid);
    const isIncomingDirect = !msg.fromMe;

    // Process if it's "Message yourself" or an incoming message to the user
    if (!isSelfChat && !isIncomingDirect) {
        return;
    }

    console.log(`\n[Inbound WhatsApp] From: ${msg.from} | Has Media: ${msg.hasMedia} | Body: "${(msg.body || '').slice(0, 50)}"`);

    try {
        let payload = {
            sender: msg.from,
            body: msg.body || ''
        };

        if (msg.hasMedia) {
            console.log('⏳ Downloading attached media from WhatsApp...');
            const media = await msg.downloadMedia();
            if (media && media.data) {
                payload.media_base64 = media.data;
                payload.media_mimetype = media.mimetype;
                payload.filename = media.filename || 'media_attachment';
                console.log(`📦 Media attached: ${media.mimetype} (${media.filename || 'unnamed'})`);
            }
        }

        console.log('🧠 Sending to FinGuard Multimodal Forensic Engine...');
        const response = await axios.post(`${BACKEND_URL}/api/whatsapp/bridge-message`, payload, {
            timeout: 120000 // 2 minute timeout
        });

        if (response.data && response.data.reply) {
            console.log(`📤 Sending reply back to WhatsApp (${response.data.type || 'verdict'})...`);
            await msg.reply(response.data.reply);
            console.log('✅ Verdict delivered to user chat!');
        }
    } catch (err) {
        console.error('❌ Error processing WhatsApp message:', err.message);
        if (err.response && err.response.data) {
            console.error('Backend details:', err.response.data);
        }
    }
}

// Listen to both 'message' (incoming) and 'message_create' (includes "Message yourself")
client.on('message', handleIncomingMessage);
client.on('message_create', handleIncomingMessage);

client.initialize().catch((err) => {
    console.error('Fatal initialization error:', err);
});
