# 📅 Google Calendar AI Agent (ADK)

A simple **AI scheduling assistant** built with **Google Agent Development Kit (ADK)** that allows users to **manage their Google Calendar using natural language**.

The agent can create, update, delete, search events, and suggest meeting times while handling **recurring meetings, attendees, and time zones automatically**.

This project demonstrates how **AI agents can perform real-world actions** by connecting an LLM to the **Google Calendar API through structured tools**.

---

## ✨ Features

- 📅 **Create events** using natural language  
- 🔄 **Update existing events**  
- ❌ **Delete calendar events**  
- 🔍 **Search and list upcoming events**  
- 🤖 **Suggest available meeting times**  
- 🔁 **Recurring meetings support (RRULE)**  
- 👥 **Add and manage attendees**  
- 🌍 **Automatic timezone handling**

---

## 🛠 Tech Stack

- **Python**
- **Google Agent Development Kit (ADK)**
- **Google Calendar API**
- **OAuth 2.0**
- **dateparser**
- **python-dateutil**
- **pytz**

---

## 🚀 Example Commands

```
Schedule a meeting tomorrow at 3pm for 1 hour
Create a weekly standup every Monday at 10am
Move my meeting with Alex to Friday at 4pm
Delete my meeting tomorrow
Find free time for a 30-minute meeting this afternoon
```

---

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd google-calendar-agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add Google API credentials

Download your **OAuth credentials** from Google Cloud Console and place the file:

```
credentials.json
```

in the project root.

### 4. Run the agent

```bash
python main.py
```

On first run, you will be prompted to authorize access to your Google Calendar.

---

## 📂 Project Structure

```
google-calendar-agent/
│
├── agent.py
├── calendar_tools.py
├── datetime_parser.py
├── recurrence_parser.py
├── main.py
├── requirements.txt
└── README.md
```

---

## 👩‍💻 Author

**Jhanvi Mistry**
