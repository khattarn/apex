# PracticeDesk — Platform Overview

## Source: workflow-diagrams.html

PracticeDesk — Feature Workflow Diagrams 
 
 
 
 

 
 PracticeDesk for Medical Professionals 
 Feature Workflow Diagrams 
 How WA AI Receptionist, Voice AI Receptionist, and Patient Booking work — step by step 
 

 
 🗂 System Overview 
 💬 WA AI Receptionist 
 📞 Voice AI Receptionist 
 📅 Patient Booking Flow 
 

 

 
 
 System Overview — Functional Decomposition 
 All three AI features and what each one does at a functional level 

 
 PracticeDesk AI Platform 
 

 
 
 💬 WA AI Receptionist 
 
 🔍 Intent Detection Identifies: book · FAQ · escalate · feedback from any message 
 ❓ FAQ Answering Hours, parking, bulk billing, referrals — instant reply from knowledge base 
 📋 Booking Collection Service → date → time → name collected conversationally 
 🔒 Manual Confirm Gate All bookings held as "pending" until you confirm in dashboard 
 🚨 Escalation Handling AI pauses; clinician gets WA alert + patient's message instantly 
 ⭐ Feedback Collection Star rating + comment after appointment complete; auto-triggered 
 
 

 
 
 📞 Voice AI Receptionist 
 
 🎙️ 24/7 Call Answering Custom greeting with clinic name & Dr's name — every call answered 
 📅 Booking over Phone Collects service, date, time, name over voice — creates pending booking 
 ❓ FAQ via Voice Hours, services, costs, directions — answered without human help 
 🚨 Emergency Escalation Detects urgency — immediate WA alert to clinician with caller's number 
 📲 Missed Call Follow-up WhatsApp message auto-sent to caller when call is not answered 
 📄 Call Transcripts Full transcript + summary stored in dashboard after every call 
 
 

 
 
 📅 Patient Booking (WA AI) 
 
 📋 Service Selection AI presents service menu; patient picks by number or name 
 📆 Date / Time Capture Asks for preference, then offers real available slots 
 👤 Patient Record Creation Name + phone auto-saved to CRM on first booking 
 ⏳ Pending Booking Created Booking held for practice review — not auto-confirmed 
 ✅ Practice Confirms One-click confirm or decline with reason in dashboard 
 💬 WA Confirmation Sent Patient gets confirmed date/time/service via WhatsApp 
 
 
 
 
 

 
 
 WhatsApp AI Receptionist — Workflow 
 How patient WhatsApp messages are received, classified, and resolved — 24 hours a day 

 
 Patient 
 WhatsApp AI 
 Practice / Dashboard 
 System / Automatic 
 

 
 
 👤 Patient 
 🤖 WhatsApp AI 
 🏥 Practice / Dashboard 
 

 
 Trigger — Inbound Message 
 
 
 Sends WhatsApp message Any time — 24 hours a day 
 
 
 Receives & identifies intent Book · FAQ · Escalate · Feedback 
 
 
 

 
 Scenario A — FAQ / General Inquiry 
 
 
 Receives instant answer Hours, parking, bulk billing, referrals, costs 
 
 
 Answers from knowledge base No human input needed. Available 24/7 
 
 
 No action required 
 
 

 
 Scenario B — Appointment Booking 
 
 
 Replies with preferences Service, date, time, name — guided step by step 
 
 
 Collects booking details Conversational — one question at a time 
 
 
 
 
 
 Receives "pending" message "The clinic will confirm shortly" 
 
 
 Creates pending booking Patient record auto-saved to CRM 
 
 
 Notification in dashboard Reviews booking · clicks Confirm or Decline 
 
 
 
 
 Receives WA confirmation Date · time · service · "See you then!" 
 
 
 Confirmation sent automatically 
 
 
 

 
 Scenario C — Escalation to Clinician 
 
 
 Requests a human Complex query, urgent matter, or distress signal 
 
 
 Pauses AI for this patient Flags conversation for manual reply 
 
 
 Instant WA alert to clinician Message text + patient number included. Clinician replies from inbox. 
 
 

 
 Scenario D — Post-Visit Feedback (Auto-triggered) 
 
 
 Receives star rating prompt Sent automatically when appointment marked complete 
 
 
 Collects rating (1–5) + comment Two-step WA conversation. Optional skip for comment. 
 
 
 Feedback in dashboard Stars + comment + patient name. Clinician alerted. 
 
 
 
 

 
 
 Voice AI Receptionist — Workflow 
 Every inbound call is answered by AI — even when you are with a patient 

 
 Patient / Caller 
 Voice AI 
 Practice / Dashboard 
 System / Automatic 
 

 
 
 📱 Patient / Caller 
 🎙️ Voice AI 
 🏥 Practice / Dashboard 
 

 
 Trigger — Inbound Call 
 
 
 Calls the clinic number Any time — practice may be busy with patients 
 
 
 AI answers instantly Custom greeting: clinic name + Dr's name + warmth 
 
 
 

 
 Scenario A — Booking over the Phone 
 
 
 States reason for call "I'd like to book a check-up for my daughter" 
 
 
 Collects booking details via voice Service · date · time · name · phone — one question at a time 
 
 
 
 
 
 Receives verbal confirmation + WhatsApp message with booking details 
 
 
 Creates pending booking Call transcript stored automatically 
 
 
 Confirms in dashboard One click · Can add clinical notes · Patient gets WA 
 
 

 
 Scenario B — FAQ (Hours, Costs, Services) 
 
 
 Asks a question "Do you do bulk billing?" / "What are your hours?" 
 
 
 Answers from knowledge base Speaks the answer · Call ends normally 
 
 
 Full transcript stored Reviewable in dashboard 
 
 

 
 Scenario C — Emergency / Escalation 
 
 
 Urgent matter or requests a human Pain, emergency, or "I need to speak to someone" 
 
 
 Detects escalation signal Politely ends call · Triggers WA alert immediately 
 
 
 Instant WA alert to clinician Caller's number included · Call back immediately 
 
 

 
 Scenario D — Missed Call / No Answer 
 
 
 Call goes unanswered / to voicemail 
 
 
 Detects no-answer outcome Sends WA follow-up to caller's mobile number 
 
 
 Missed call logged in dashboard 
 
 
 
 
 Receives WA: "Sorry we missed you" Can book or ask questions via WhatsApp 
 
 
 
 
 
 

 
 
 Patient Booking via WhatsApp AI — Detailed User Flow 
 From the first patient message to a confirmed appointment 

 

 
 
 End-to-End Flow 
 

 
 1 
 
 Patient 
 Sends WhatsApp message to clinic 
 "Hi, I need to see a dentist for a check-up" — any natural language works 
 
 

 
 2 
 
 WhatsApp AI 
 Greets patient & shows services 
 Displays service menu: Check-up · Filling · Extraction · Clean & Polish… 
 
 

 
 3 
 
 Patient 
 Selects a service 
 Replies "1" or types "Check-up" 
 
 

 
 4 
 
 WhatsApp AI 
 Asks for preferred date and time 
 "What date works for you? Morning or afternoon?" 
 
 

 
 5 
 
 Patient 
 Gives date preference 
 "Thursday afternoon" 
 
 

 
 6 
 
 WhatsApp AI 
 Offers real available slots 
 "We have Thursday at 2pm or 4pm. Which works for you?" 
 
 

 
 7 
 
 Patient 
 Confirms a slot 
 "2pm please" 
 
 

 
 8 
 
 WhatsApp AI 
 Asks for full name 
 "Great! Can I also get your full name?" 
 
 

 
 9 
 
 Patient 
 Provides name 
 "James Chen" 
 
 

 
 10 
 
 WhatsApp AI 
 Creates pending booking 
 Booking saved · Patient record auto-created in CRM · Practice notified 
 
 

 
 11 
 
 Practice 
 Reviews & confirms in dashboard 
 One click · Can add clinical notes · Can decline with reason 
 
 

 
 12 
 
 Patient 
 Receives WhatsApp confirmation 
 "Confirmed! Thursday 2pm — Check-up. See you then! Reply CANCEL if needed." 
 
 

 
 

 
 
 WhatsApp Conversation Preview 
 
 
 🏥 
 
 City Dental Clinic 
 ● Online 
 
 
 
 Hi, I need to see a dentist. Any appointments this week? 8:41 AM 
 Hi! I can help you book. We offer: 1. Check-up (30 min, ₹800) 2. Clean & Polish (45 min, ₹1,200) 3. Filling (45 min, ₹1,500) Which service do you need? 8:41 AM ✓✓ 
 Check-up please 8:42 AM 
 What date works for you? Morning or afternoon? 8:42 AM ✓✓ 
 Thursday afternoon 8:42 AM 
 We have Thursday at 2pm or 4pm. Which works for you? 8:43 AM ✓✓ 
 2pm — James Chen 8:43 AM 
 Thank you James! Your appointment request for Thursday 2pm (Check-up) has been received. The clinic will confirm shortly. ✅ 8:43 AM ✓✓ 
 ✅ Confirmed! Your Check-up is booked for Thursday 5 June at 2pm. See you then! Reply CANCEL if plans change. 9:15 AM ✓✓ 
 
 

 
 🔒 Manual Confirm Mode 
 The AI never auto-confirms appointments. Every booking is held as "pending" until you click Confirm in your dashboard. You stay in control of your schedule. 
 

 
 👤 Auto Patient Record 
 Name, phone, visit history, and preferred practitioner are all captured automatically from the first booking — no data entry needed. 
 

 
 ⭐ Automatic Feedback Request 
 When you mark an appointment as complete, a star rating prompt is sent automatically to the patient. Ratings appear in your dashboard.