# Chat Analytic 💬🔥

An evidence-driven, savage group chat, private DM, and social identity profiling analyst. Inspired by the **"What Brandon Thinks"** project, this application parses raw WhatsApp chat exports and uses a lightweight local analytical pipeline coupled with Gemini models to construct hilarious, painfully accurate, and brutally honest social reports.

---

## ✨ Features & Capabilities

### 1. Three Analysis Modes
* **What People Think of You**: Brutally profiles a single target user's texting habits, tone, and pacing across multiple private and group chats—completely anonymously.
* **DM Mode (1-on-1 Dynamic)**: Characterizes the unspoken pacing, initiation ratios, reply asymmetry, and conversational chemistry of a private chat between two people.
* **Group Mode (The Suspects & Dynamics)**: Summarizes the group essence, roasts the collective dynamic, maps out interpersonal pairings, and profiles individual group members.

### 2. Analytical Engine
* **5-Signal Hot Moment Detection**: Replaces basic volume counts with a sliding-window engine that scores bursts of activity across five metrics:
  * 📈 **Volume Spike**: Conversational density exceeding baseline.
  * ⚡ **Velocity Spike**: High message frequency in a short burst (e.g. 4+ messages in 3 minutes).
  * 🗣 **Monologue Alert / Turn-Taking Collapse**: A single user spamming consecutive messages.
  * 🏓 **Rapid-Fire Replies / Response Compression**: Fast-paced back-and-forth conversational exchanges (avg reply gap < 45 seconds).
  * 🎯 **Topic Cluster**: High frequency of short, rapid-fire ping-pong texts.
* **Collapsible Lead-up (Pre-context)**: Extracts the preceding messages directly before a hot moment occurs so the commentator understands the exact catalyst of the drama.
* **The Story So Far (Chapter Narrative)**: Converts raw chat density trends into a cinematic, 4-phase timeline:
  * 🌱 **Setup** (The Early Phase)
  * 📈 **Rising** (The Escalation)
  * 🔥 **Peak** (Peak Chaos/Spam/Drama)
  * 🌅 **Aftermath** (Wind-down/Current State)
* **Final Verdicts**: A single, observational closing blow summarising the relationship, ego profile, or group chat.

### 3. Premium Responsive Dashboard
* Custom HSL dark-theme React interface with dynamic glow styling, custom Lucide icons, and interactive charts.
* Color-coded incident badges and collapsible lead-up blocks for notable events.
* **Static Archiving (HTML Export)**: Save your reports directly to disk. Generates a self-contained offline HTML report styled with Tailwind CSS, ready to share or archive.

---

## 🛠️ Architecture & Tech Stack

The app operates on a **DB-less, zero-persistence ephemeral architecture** for maximum privacy:

* **Backend**: FastAPI (Python 3.10+)
  * Handles chat tokenization, statistical analyses, reply matrices, initiation baselines, and multi-signal scoring in-memory.
  * Prompts are written in a lean, direct commentary style utilizing the `google-genai` SDK.
* **Frontend**: React (Vite + TypeScript)
  * Rendered as an interactive dashboard showing timelines, charts, profiles, and timelines.
  * Uses Tailwind CSS for premium responsive styling.

---

## 🚀 Setup & Installation

### Prerequisites
* Python 3.10+
* Node.js 18+
* A **Gemini API Key** (from Google AI Studio)

---

### Step 1: Clone and Configure the Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create your `.env` file from the example:
   ```bash
   cp .env.example .env
   ```
3. Open `.env` and add your Gemini API Key:
   ```env
   GEMINI_API_KEY=YOUR_ACTUAL_GEMINI_API_KEY
   LOG_LEVEL=DEBUG
   ```
4. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Start the FastAPI backend server:
   ```bash
   uvicorn main:app --reload
   ```
   The backend will run on `http://127.0.0.1:8000`.

---

### Step 2: Configure and Run the Frontend

1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Start the Vite React development server:
   ```bash
   npm run dev
   ```
   Open `http://localhost:5173` in your web browser.

---

## 📂 Exporting WhatsApp Chats

To generate a report, upload your raw WhatsApp `.txt` file export:
1. **On Mobile (iOS/Android)**: Open the chat info page, scroll down, select **Export Chat**, and choose **Without Media**.
2. **On Web/Desktop**: Export the chat history as a plain text file.
3. Drag and drop the `.txt` file into the Chat Analytic dashboard to instantly start the analysis.

---

## 🔒 Privacy & Data Anonymity
* Since the project runs entirely locally and in-memory, **your chat logs never touch a database or persistent server**.
* Prompts are strictly structured to characterize the chats anonymously without hardcoding user identities or tracking personal information.
