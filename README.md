# 🌾 KrishiSignal AI — Context-Aware Crop Protection Command Center
### *Precision Agricultural Risk Scoring & Multi-Channel Campaign Orchestrator*
**Production Space:** [huggingface.co/spaces/Sarthak5628/agrisignal](https://huggingface.co/spaces/Sarthak5628/agrisignal)

---

## 1. System Vision & Architecture

KrishiSignal AI is a precision agricultural marketing command center. Instead of blasting generic product promotions to all farmers, the system uses data fusion to dynamically coordinate campaigns based on:
1.  **Biological Urgency:** Sowing dates, growth stages, and live humidity/temperature disease vectors.
2.  **Operational Inventory:** Verified local retailer stock counts.
3.  **Hardware Profiling:** Routing rich WhatsApp media to smartphones, direct text SMS to keypad phones, and generating Voice IVR scripts for low-literacy segments.

```text
[Frontend: Dark-Mode Dashboard (HTML5 / Vanilla JS / Leaflet.js)]
          | 
          | (Rest APIs: /api/risk-zones, /api/stats, /api/generate-campaign)
          v
[Backend: FastAPI (Python 3.12) - Running Locally and on HF Spaces]
          |
          +--> [Data Layer: Pandas] (Matches growers to closest retailers via coordinates)
          +--> [Weather Client: HTTPX / Open-Meteo] (Queries live climate conditions)
          +--> [GenAI Engine: Gemini 2.5 Flash] (Generates copy in 6 vernaculars)
          +--> [Visual Engine: Pollinations Turbo] (Downloads, caches, and base64 encodes graphics)
          +--> [Telecom Engine: Twilio API] (Executes live Call, SMS, and WhatsApp MMS dispatches)
```

---

## 2. Dynamic Priority Scoring Algorithm

The engine calculates a dynamic **Priority Score** (0-100) for each district to prioritize campaign delivery:

$$P = \min\left(100, 100 \times \left[ S_r \times 0.40 + W_r \times 0.30 + E_h \times 0.20 + I_s \times 0.10 \right]\right)$$

### 1. Metric Weights:
*   **Crop Stage Vulnerability ($S_r$ - 40%):** Risk factors mapped to the active growth stage (e.g. wheat tillering = 0.85; flowering = 0.75; vegetative = 0.50).
*   **Weather Pathogen Suitability ($W_r$ - 30%):** Driven by relative humidity (RH) thresholds.
    *   $\text{RH} \ge 80\% \rightarrow W_r = 0.95$ (Critical fungal spread conditions)
    *   $\text{RH} \ge 70\% \rightarrow W_r = 0.75$
    *   $\text{RH} \ge 60\% \rightarrow W_r = 0.50$
    *   $\text{RH} \ge 50\% \rightarrow W_r = 0.25$
    *   $\text{RH} < 50\% \rightarrow W_r = 0.05$ (Fungus inactive / dry air suppression)
    *   *Modifiers:* Temperature optimal window ($15^\circ\text{C}-25^\circ\text{C}$ multiplies risk by $1.2$), extreme heat ($>35^\circ\text{C}$ multiplies risk by $0.5$), and active rainfall adds $+0.12$.
*   **Historical Click Engagement ($E_h$ - 20%):** Calculated from average historical click-through rates.
*   **Inventory Gating ($I_s$ - 10%):** Set to 0.9 if local stock is sufficient, else 0.4 (low stock penalty).

### 2. Statistical Confidence Margin:
To normalize data quality across districts with varying farmer sample sizes ($n$), the engine calculates a 95% confidence interval margin:

$$\text{Confidence Margin} = \max\left(2.0, \min\left(15.0, 1.96 \times \sqrt{\frac{P \times (100 - P)}{n}}\right)\right)$$

---

## 3. Operational Features

### A. Automatic Inventory Gating
To protect marketing spend, consumer campaigns are blocked if local retailer stock is $< 10$ units. The system instead generates a B2B Retailer Restock Alert containing the number of at-risk farmers and recent POS sales volume to motivate restocking.

### B. Hardware Segment Routing
*   **WhatsApp Route:** Rich vernacular copy paired with base64 campaign visuals.
*   **SMS Route:** Compressed vernacular text limited strictly to **130 characters** to ensure safe delivery across cellular grids.
*   **Voice IVR Route:** Conversational audio script generated in regional dialect for phone outreach.

### C. Live Telephony Integrations (Twilio API)
*   **Real Voice Outbound Calls:** Features dynamic accent mapping (Latin/Hinglish routes to Polly Raveena/Aditi voices; Indic scripts route to Alice regional voice) and UTF-8 TwiML XML pre-declaration headers to guarantee Indic letters are pronounced clearly without robotic failure.
*   **WhatsApp MMS Visual Attachment:** Attaches the public image generation URL to Twilio's WhatsApp payload, delivering the visual directly into the user's phone.
*   **Interactive Trial Gate Modal:** Frontend intercepts Twilio validation restrictions (unverified trial caller ID) and guides the user on sandbox join parameters and OTP registrations.

---

## 4. REST API Reference

*   `GET /api/risk-zones` - Returns all district risk summaries, including coordinates, scores, confidence margins, weather, and reach metrics.
*   `GET /api/stats` - Returns aggregated metrics for the top dashboard navigation bar (Critical Zones, High Zones, Total At-Risk Farmers, and Reach by channel).
*   `GET /api/retailer-alerts` - Returns list of B2B restock alerts.
*   `POST /api/generate-campaign` - Accepts `{"district": "District Name"}`. Runs the gating check and calls the Gemini/Pollinations pipeline to return the complete campaign package.
*   `POST /api/dispatch/whatsapp` - Routes bulk WhatsApp campaign messages (including optional AI-generated public image URLs).
*   `POST /api/dispatch/sms` - Sends bulk SMS advisories using Twilio.
*   `POST /api/dispatch/call` - Triggers outbound call with custom vernacular speech TwiML responses.

---

## 5. Local Setup & Execution

### Prerequisites:
*   Python 3.12+ installed.

### Installation:
1. Clone the repository and navigate to the project folder:
   ```bash
   git clone https://github.com/23f3000340/Kisanpulse.git
   cd Kisanpulse
   ```
2. Setup a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r kisanpulse/requirements.txt
   ```
4. Set up environment variables inside `kisanpulse/.env`:
   ```env
   # Generative AI Key
   GEMINI_API_KEY=your_gemini_api_key_here

   # Twilio Configuration (Required for Live Calling/SMS/WhatsApp)
   TWILIO_ACCOUNT_SID=your_twilio_sid_here
   TWILIO_AUTH_TOKEN=your_twilio_token_here
   TWILIO_FROM_NUMBER=your_twilio_purchased_number_here
   TWILIO_WHATSAPP_FROM_NUMBER=+14155238886 # Keep +14155238886 for Sandbox testing
   ```

### Running Locally:
Run the FastAPI server from the `kisanpulse` directory:
```bash
cd kisanpulse
python main.py
```
Open your browser and navigate to:
```text
http://localhost:8000/static/index.html
```
*(Ensure you enable Geo Permissions for India under **Messaging Settings** and **Voice Settings** in your Twilio Console to bypass Trial Account restrictions.)*
