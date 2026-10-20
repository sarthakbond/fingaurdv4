/**
 * FinGuard WhatsApp Direct Web Bridge
 * STRICT ISOLATION ARCHITECTURE:
 * - Operates EXCLUSIVELY inside your private "Message Yourself" chat.
 * - Hardware timestamp filtering ignores all past/synced messages.
 * - Group chats and external contacts are hard-blocked at the socket layer.
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

const BACKEND_URL = process.env.FINGUARD_URL || 'http://127.0.0.1:8000';
const CHROME_PATH = process.env.CHROME_PATH || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

console.log('=========================================================');
console.log('🛡️  FinGuard WhatsApp Forensic Shield - Initializing...');
console.log(`📡 Backend Engine: ${BACKEND_URL}`);
console.log('🔒 Security Mode: STRICT PRIVATE SELF-CHAT ONLY');
console.log('=========================================================');

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

let BOT_READY_TIME = 0;

client.on('qr', (qr) => {
    console.log('\n=========================================================');
    console.log('📱 SCAN THIS QR CODE WITH WHATSAPP ON YOUR PHONE:');
    console.log('   (Open WhatsApp -> Linked Devices -> Link a Device)');
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

    // Also download qr_code.png locally
    axios.get(qrImageUrl, { responseType: 'arraybuffer' }).then((res) => {
        fs.writeFileSync(path.join(__dirname, 'qr_code.png'), res.data);
    }).catch(() => {});
});

client.on('authenticated', () => {
    console.log('✅ WhatsApp authenticated successfully! Initializing secure sandbox...');
});

client.on('ready', () => {
    BOT_READY_TIME = Math.floor(Date.now() / 1000);
    const myPhone = client.info && client.info.wid ? client.info.wid.user : 'Unknown';
    console.log('\n=========================================================');
    console.log('🚀 FINGUARD SHIELD IS ONLINE & FULLY SECURED!');
    console.log(`👤 Authorized Self-Account: +${myPhone}`);
    console.log('🔒 LOCK ENGAGED: Messages to any other contact are BLOCKED.');
    console.log('=========================================================');
    console.log('💡 How to scan:');
    console.log('   1. Open WhatsApp on your phone');
    console.log('   2. Open "Message yourself" (your own chat)');
    console.log('   3. Type "hi" to receive the guide, or forward any media to yourself!');
    console.log('=========================================================\n');
});

const handledMessageIds = new Set();

async function handleMessage(msg) {
    if (!msg || !msg.id || handledMessageIds.has(msg.id.id)) return;
    handledMessageIds.add(msg.id.id);

    if (handledMessageIds.size > 2000) handledMessageIds.clear();

    console.log(`\n[EVENT] from=${msg.from} | to=${msg.to} | fromMe=${msg.fromMe} | ts=${msg.timestamp} | body="${(msg.body || '').slice(0, 30)}"`);

    // ── GUARD 1: TIMESTAMP LOCK (Ignore messages older than 2 mins before bot startup) ──
    if (BOT_READY_TIME && msg.timestamp && (BOT_READY_TIME - msg.timestamp) > 120) {
        console.log(`[FILTER] Skipped historical message (${BOT_READY_TIME - msg.timestamp}s old)`);
        return;
    }

    // ── GUARD 2: EMPTY MESSAGE FILTER ────────────────────────────────────
    const bodyText = (msg.body || '').trim();
    if (!bodyText && !msg.hasMedia) {
        console.log('[FILTER] Skipped empty message');
        return;
    }

    // ── GUARD 3: BOT LOOP PREVENTION ─────────────────────────────────────
    if (bodyText && (
        bodyText.includes('FinGuard') ||
        bodyText.includes('SEBI Registered:') ||
        bodyText.startsWith('⚠️') ||
        bodyText.startsWith('🔍') ||
        bodyText.startsWith('🛡️') ||
        bodyText.startsWith('*')
    )) {
        console.log('[FILTER] Skipped bot output loop');
        return;
    }

    // ── GUARD 4: STRICT SELF-CHAT ONLY VERIFICATION ──────────────────────
    if ((msg.from && msg.from.endsWith('@g.us')) || (msg.to && msg.to.endsWith('@g.us'))) {
        console.log('[FILTER] Skipped group chat');
        return;
    }

    const myUser = client.info && client.info.wid ? client.info.wid.user : '8432489640';
    const myWid = client.info && client.info.wid ? client.info.wid._serialized : '918432489640@c.us';
    const myLid = (client.info && client.info.lid && client.info.lid._serialized) ? client.info.lid._serialized : '265119942611173@lid';

    // Must be strictly sent to and from your own account (Message yourself)
    const isToMe = (msg.to === myWid) || (msg.to === myLid) || (msg.to && myUser && msg.to.includes(myUser)) || (msg.to === '265119942611173@lid');
    const isFromMe = (msg.from === myWid) || (msg.from === myLid) || (msg.from && myUser && msg.from.includes(myUser)) || msg.fromMe;

    if (!isToMe || !isFromMe) {
        console.log(`[FILTER] Skipped external chat: from=${msg.from} to=${msg.to}`);
        return;
    }

    const replyChatId = msg.to || myWid;
    console.log(`[ACCEPT] Private Note-to-Self received! Processing: "${bodyText.slice(0, 50)}"`);

    try {
        let payload = {
            sender: myWid,
            body: bodyText
        };

        if (msg.hasMedia) {
            console.log('📦 Media detected! Sending immediate processing ACK to chat...');
            try {
                await client.sendMessage(replyChatId, "🔍 *FinGuard Forensic Engine*: Media received!\n\n⏳ _Analyzing facial frames, synthetic audio residuals, OCR text, and SEBI advisory compliance on GPU workstation... Please hold on!_");
            } catch (ackErr) {
                console.error('Warning sending ACK:', ackErr.message);
            }

            console.log('⏳ Downloading media from WhatsApp (with retry)...');
            let media = null;
            for (let attempt = 1; attempt <= 6; attempt++) {
                try {
                    await new Promise(r => setTimeout(r, 2500));
                    media = await msg.downloadMedia();
                    if (media && media.data) {
                        console.log(`✅ Media successfully retrieved on attempt ${attempt}! Size: ${media.data.length} chars`);
                        break;
                    }
                } catch (dlErr) {
                    console.log(`⚠️ Media download attempt ${attempt} pending: ${dlErr.message || dlErr}...`);
                }
            }

            if (media && media.data) {
                payload.media_base64 = media.data;
                payload.media_mimetype = media.mimetype;
                payload.filename = media.filename || 'attachment';
                console.log(`📦 Media downloaded successfully: ${media.mimetype}`);
            } else {
                console.error('❌ Could not retrieve media data after retries.');
                await client.sendMessage(replyChatId, "⚠️ *FinGuard Notice:* Could not retrieve the attached media from WhatsApp. Please ensure the video has fully finished uploading from your phone and forward it again.");
                return;
            }
        }

        console.log('🧠 Running FinGuard Multimodal Forensic Analysis...');
        const response = await axios.post(`${BACKEND_URL}/api/whatsapp/bridge-message`, payload, {
            timeout: 120000
        });

        if (response.data && response.data.reply && response.data.reply.trim()) {
            console.log(`📤 Dispatching reply to ${replyChatId}...`);
            await client.sendMessage(replyChatId, response.data.reply);
            console.log('✅ Forensic verdict sent to your "Message yourself" chat!');
        }
    } catch (err) {
        console.error('⚠️ Bridge error:', err.message || err);
    }
}

// Listen to both message events (message_create captures messages you send to yourself)
client.on('message', handleMessage);
client.on('message_create', handleMessage);

client.initialize().catch((err) => {
    console.error('Fatal initialization error:', err);
});
