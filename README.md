# NewSite Estate Management Portal

A secure, cloud-based estate management and web automation prototype built specifically for **NewSite Estate**. This solution automates resident onboarding, centralizes levy tracking, secures portal entry logs, and streamlines communication between the EXCO Admin and homeowners.

---

## 🚀 Key Features

* **Admin Control Center:** Provision resident credentials, track automated occupant metrics, manage property active lists, and toggle suspension status.
* **Homeowner Portal:** Secure dashboard displaying personalized transaction logs, payment verification histories, and localized utility complaints tracking.
* **Official Broadcast Board:** Real-time bulletin interface for pinning critical, labeled estate updates (General, Security, Maintenance, Finance) from the EXCO.
* **Security Guardrails:** Full role-based authentication (RBAC) separating administrative powers from resident views, with absolute session tracking and auto-suspension capabilities on resident offboarding.

---

## 🛠️ Tech Stack & Architecture

* **Backend Engine:** Python 3.10+ / Flask framework
* **Database Layer:** SQLite Engine utilizing Flask-SQLAlchemy (ORM architecture)
* **Authentication Management:** Cryptographic credential hashing via Werkzeug security & Flask-Login session cookies
* **Frontend Design Layer:** Tailwind CSS framework responsive mapping

---

## 💻 Local Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/Ghentlesteve/Estate-management-system.git](https://github.com/Ghentlesteve/Estate-management-system.git)
   cd YOUR_REPO_NAME

**Establish a virtual environment:**
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

**Install dependencies:**
pip install -r requirements.txt

**Initialize database & start the application:**
python app.py
Open http://127.0.0.1:5000 inside your preferred browser.



