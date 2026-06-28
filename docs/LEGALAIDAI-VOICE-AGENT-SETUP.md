# LegalAidAI — Dedicated Voice Agent Setup
## Technical Handover: Vobiz + Dograh Integration

**Prepared by:** Neeraj Khattar  
**Date:** 2026-06-16  
**Purpose:** Set up a dedicated Indian phone number with an AI voice agent for LegalAidAI's administrative and customer service function, using the existing Vobiz and Dograh accounts already provisioned for the portfolio.

---

## What You Are Building

A dedicated Indian phone number (e.g. +91 XXXXXXXXXX) that:
- **Inbound:** When any user/advocate calls the number, an AI voice agent answers — handles FAQs, subscription queries, account help, escalation
- **Outbound:** The platform can programmatically trigger the AI to call a user/advocate (welcome calls, payment reminders, trial expiry notices, etc.) with the LegalAidAI number showing as caller ID
- **No hardware required** — runs entirely via SIP trunk (Vobiz) and AI voice platform (Dograh)

---

## Existing Accounts (already provisioned — request credentials from Neeraj)

| Service | What it does | Account |
|---|---|---|
| **Vobiz** | Indian SIP trunk provider — holds the +91 phone number, routes calls | `edcf4901.sip.vobiz.ai` |
| **Dograh** | AI voice agent platform — runs the conversation workflow | `app.dograh.com` |

The PracticeDesk product already has one India number (+91 9262171423) running this exact stack. This setup replicates that pattern with a new number and a new agent.

---

## Step 1 — Provision a New Indian Phone Number on Vobiz

1. Log in to Vobiz → **Numbers** → **Buy / Port Number**
2. Select India (+91), choose a city/area code appropriate for LegalAidAI's audience
3. Purchase the number — note the full number in E.164 format (e.g. `+91 9XXXXXXXXX`)
4. You will need this number in **two formats** throughout this setup:
   - **International format:** `00919XXXXXXXXX` (used for inbound DID routing)
   - **Local digits only:** `9XXXXXXXXX` (used in Dograh telephony config for outbound caller ID)

> **Why two formats?** Vobiz registers the DID in international format but prepends `91` automatically when presenting outbound caller ID. If you give it `919XXXXXXXXX`, it becomes `91919XXXXXXXXX` — wrong. Give it only the local digits and it produces `919XXXXXXXXX` correctly.

---

## Step 2 — Create a SIP Account on Vobiz

This is the credential set the Dograh Voice Application will use to authenticate with Vobiz.

1. Vobiz → **SIP Accounts** → **Create**
2. Name: `legalaidai-voice` (or similar)
3. Note down:
   - **SIP Username** (e.g. `legalaidai-voice`)
   - **SIP Password** (generate a strong one)
   - **SIP Domain:** `edcf4901.sip.vobiz.ai`
   - **Transport:** TCP (required — Vobiz UDP is unreliable with cloud platforms)

---

## Step 3 — Create a Voice Application on Vobiz

The Voice Application connects your DID number to an Answer URL (Dograh's inbound webhook). You will fill in the Answer URL in Step 6 after creating the Dograh agent.

1. Vobiz → **Voice Applications** → **Create**
2. Name: `legalaidai-agent` (or similar)
3. **Answer URL:** leave blank for now — fill in after Step 6
4. **Method:** POST
5. **SIP Account:** select the `legalaidai-voice` account created above

---

## Step 4 — Assign the DID to the Voice Application

1. Vobiz → **Numbers** → find your new number
2. **Edit** → set **Voice Application** to `legalaidai-agent`
3. Save

Now any inbound call to this number will fire the Answer URL you set in Step 3.

---

## Step 5 — Create the AI Agent in Dograh

> **Critical:** Use **Agent Builder** (not Blank Canvas). Blank Canvas creates an empty workflow with no nodes — calls will connect and immediately hang up.

1. Log in to Dograh (`app.dograh.com`) → **Agents** → **Create Agent**
2. Choose: **Agent Builder** (the template option)
3. Name: `LegalAidAI Voice Agent` (or `Nyaya Saathi Voice`)
4. Configure the agent:
   - **Language:** Hindi + English (bilingual — agent should detect caller language and respond accordingly)
   - **Voice:** choose an Indian-accented voice if available
   - **System prompt:** see suggested prompt below
5. Save the agent
6. Note the **Workflow Integer ID** from the URL bar (e.g. `app.dograh.com/agents/XXXX` — the number is `XXXX`)
7. Note the **Workflow UUID** from Settings → API or from the trigger URL shown in the agent

### Suggested System Prompt

```
You are the voice assistant for LegalAidAI (also known as Nyaya Saathi), 
an AI-powered legal services platform serving Indian citizens, advocates, 
and corporates.

Your role is to help callers with:
- Information about subscription plans (₹2,500/month first month, ₹5,000/month renewal for advocates)
- Account and billing queries
- How to use the platform's features (legal Q&A, case tracking, WhatsApp assistance)
- Escalation to a human team member when needed

Speak in the caller's preferred language — Hindi or English. If the caller 
starts in Hindi, respond in Hindi. If English, respond in English.

Keep responses concise — this is a phone call, not a chat session. 
Do not read out long lists; summarise and offer to follow up via WhatsApp.

If you cannot resolve the query, take the caller's number and tell them 
a team member will call back within 2 business hours.

You are a professional assistant. Never reveal that you are an AI system 
or name the underlying technology platform. If asked, say you are the 
LegalAidAI customer support line.
```

---

## Step 6 — Add Vobiz as a Telephony Provider in Dograh

1. Dograh → **Settings** → **Telephony** → **Add Configuration**
2. Provider: **Vobiz** (or SIP/BYOT depending on Dograh's UI)
3. Enter credentials from Step 2:
   - SIP Username: `legalaidai-voice`
   - SIP Password: (the one you set)
   - SIP Domain: `edcf4901.sip.vobiz.ai`
   - Transport: TCP
4. **From Number / Caller ID field:** enter the number in **local digits only** — e.g. `9XXXXXXXXX` (no `+`, no `91`, no `0091`)
   - This is the critical field. Vobiz will prepend `91` itself. If you put `919XXXXXXXXX`, calls will fail with "from number not owned by this account"
5. Save — note the **Telephony Config ID** (integer) shown after saving

---

## Step 7 — Wire Inbound: Set the Dograh Answer URL in Vobiz

The inbound webhook URL format is:
```
https://api.dograh.com/api/v1/telephony/inbound/{WORKFLOW_INTEGER_ID}
```

Where `{WORKFLOW_INTEGER_ID}` is the integer from Step 5 (e.g. `6500`).

> **Critical URL format gotchas:**  
> ✓ `https://api.dograh.com/api/v1/telephony/inbound/6500` ← correct  
> ✗ `https://api.dograh.com/api/v1/telephony/inbound/run?workflow_id=6500` ← wrong (404)  
> ✗ `https://api.dograh.com/api/v1/telephony/inbound?workflow_id=6500` ← wrong (422)  
> The workflow ID must be an integer path parameter, not a query string.

1. Return to Vobiz → **Voice Applications** → `legalaidai-agent` → **Edit**
2. Set **Answer URL** to: `https://api.dograh.com/api/v1/telephony/inbound/{WORKFLOW_INTEGER_ID}`
3. Save

**Test inbound:** Call the new number from any phone. The Dograh agent should answer within 2–3 rings.

---

## Step 8 — Test & Verify Outbound Caller ID

Trigger a test outbound call via the Dograh API:

```bash
curl -X POST "https://app.dograh.com/api/v1/public/agent/workflow/{WORKFLOW_UUID}" \
  -H "X-API-Key: {DOGRAH_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919810982019",
    "telephony_configuration_id": {TELEPHONY_CONFIG_ID}
  }'
```

Replace `{WORKFLOW_UUID}`, `{DOGRAH_API_KEY}`, `{TELEPHONY_CONFIG_ID}` with your values.

Check:
1. The call connects and the agent speaks ✓
2. Caller ID shown on the recipient's phone is the LegalAidAI number ✓

If caller ID is wrong (e.g. shows a US or unrecognised number), revisit Step 6 — the "from number" field format is the usual cause.

---

## Step 9 — Integrate Outbound Calls from LegalAidAI Codebase

Since LegalAidAI runs on **Netlify Functions (Node.js)**, outbound calls are triggered from a serverless function. Add the following:

### Environment Variables (Netlify Dashboard → Site Settings → Environment)

```
DOGRAH_API_KEY=<from Dograh Settings>
DOGRAH_LEGALAIDAI_WORKFLOW_UUID=<UUID from Step 5>
DOGRAH_LEGALAIDAI_TELEPHONY_CONFIG_ID=<integer from Step 6>
```

### Netlify Function: `trigger-voice-call.js`

```javascript
// netlify/functions/trigger-voice-call.js

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: 'Method Not Allowed' }
  }

  const { phone_number, contact_name, query_type, lead_id } = JSON.parse(event.body || '{}')

  if (!phone_number) {
    return { statusCode: 400, body: JSON.stringify({ error: 'phone_number required' }) }
  }

  const payload = {
    phone_number,                        // E.164 format, e.g. "+919810982019"
    telephony_configuration_id: parseInt(process.env.DOGRAH_LEGALAIDAI_TELEPHONY_CONFIG_ID),
    initial_context: {                   // Agent can reference these via {{initial_context.field}}
      contact_name: contact_name || '',
      query_type:   query_type   || 'general',
      lead_id:      lead_id      || '',
    }
  }

  const resp = await fetch(
    `https://app.dograh.com/api/v1/public/agent/workflow/${process.env.DOGRAH_LEGALAIDAI_WORKFLOW_UUID}`,
    {
      method: 'POST',
      headers: {
        'X-API-Key':    process.env.DOGRAH_API_KEY,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    }
  )

  if (!resp.ok) {
    const err = await resp.text()
    console.error('Dograh error:', err)
    return { statusCode: 502, body: JSON.stringify({ error: 'Call initiation failed', detail: err }) }
  }

  const result = await resp.json()
  return {
    statusCode: 200,
    body: JSON.stringify({ success: true, workflow_run_id: result.workflow_run_id })
  }
}
```

### Calling from your frontend or other functions

```javascript
// Example: trigger a welcome call after new advocate signs up
await fetch('/.netlify/functions/trigger-voice-call', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    phone_number: '+91' + advocatePhone,  // ensure E.164
    contact_name: advocateName,
    query_type:   'welcome',
    lead_id:      advocateId,
  })
})
```

---

## Step 10 — Optional: Dograh Webhook for Call Completion

Dograh can POST a webhook when each call ends, giving you the transcript, recording URL, and call outcome. This lets you log calls in Firebase Firestore.

1. Dograh → Agent Settings → **Webhook URL**
2. Set to: `https://www.legalaidai.in/.netlify/functions/dograh-webhook`

### Netlify Function: `dograh-webhook.js`

```javascript
// netlify/functions/dograh-webhook.js
const admin = require('firebase-admin')

// initialise Firebase Admin once
if (!admin.apps.length) {
  admin.initializeApp({ credential: admin.credential.cert(JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT)) })
}
const db = admin.firestore()

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') return { statusCode: 405, body: 'Method Not Allowed' }

  const payload = JSON.parse(event.body || '{}')
  const { workflow_run_id, initial_context, transcript_url, recording_url } = payload
  const lead_id = initial_context?.lead_id

  if (lead_id) {
    await db.collection('voice_call_logs').add({
      lead_id,
      workflow_run_id,
      transcript_url,
      recording_url,
      created_at: admin.firestore.FieldValue.serverTimestamp(),
    })
  }

  return { statusCode: 200, body: 'ok' }
}
```

---

## Summary Checklist

- [ ] New +91 number purchased on Vobiz
- [ ] SIP account `legalaidai-voice` created on Vobiz
- [ ] Voice Application `legalaidai-agent` created on Vobiz (Answer URL blank for now)
- [ ] DID assigned to Voice Application
- [ ] Dograh agent created using **Agent Builder** (not blank canvas)
- [ ] Workflow Integer ID and UUID noted
- [ ] Vobiz telephony config added in Dograh — "from number" as local digits only (e.g. `9XXXXXXXXX`)
- [ ] Telephony Config ID noted
- [ ] Vobiz Answer URL updated: `https://api.dograh.com/api/v1/telephony/inbound/{WORKFLOW_INTEGER_ID}`
- [ ] Inbound test: called number → agent answered ✓
- [ ] Outbound test: curl trigger → correct +91 caller ID on recipient's phone ✓
- [ ] Environment variables added to Netlify
- [ ] `trigger-voice-call.js` function deployed
- [ ] (Optional) `dograh-webhook.js` function deployed and wired in Dograh

---

## Key Gotchas — Lessons from PracticeDesk Setup

| Pitfall | What happens | Fix |
|---|---|---|
| Blank Canvas in Dograh | Agent exists but workflow has no nodes — call connects and hangs up immediately | Always use **Agent Builder** template |
| Wrong inbound URL format | 404 or "phone number not configured" error | URL must be `.../inbound/{integer}` not `.../inbound/run` or query string |
| Wrong "from number" format in Dograh | "from number 91919XXXXXXXXX not owned" error | Store local digits only: `9XXXXXXXXX` (Vobiz prepends `91` automatically) |
| UDP transport on Vobiz | Registration failures from cloud platforms | Always use **TCP** for SIP transport |
| Telephony config not specified in API call | Dograh uses its default config — may route via wrong number/carrier | Always pass `telephony_configuration_id` explicitly in every outbound API call |

---

## Credentials to Request from Neeraj

- Vobiz account login (to provision the new number and SIP account)
- Dograh account login (to create the new agent)
- Dograh API Key (for outbound call triggers from Netlify functions)

The existing `DOGRAH_API_KEY` in the Apex `.env` can be reused — it is account-level, not agent-specific.
