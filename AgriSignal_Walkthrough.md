# AgriSignal — Product Walkthrough
### AI-Powered Agricultural Marketing Platform | Built for Syngenta Hackathon 2026

---

## What is AgriSignal?

AgriSignal is an **autonomous marketing command center** for Syngenta's marketing team. It replaces Excel sheets and gut-feel decisions with a live, data-driven dashboard that tells the marketing team exactly:

- **Which farmers** are at biological risk right now
- **What product** to recommend and why
- **Which channel** to use (WhatsApp, SMS, or Voice) based on the farmer's device
- **When to send** based on historical engagement patterns
- **Whether stock exists** before a single message is dispatched

It runs on Syngenta's own internal data — no assumptions, no fabrications.

---

## The Problem It Solves

Syngenta's marketing team today sends campaigns manually. A manager in Pune decides "let's push Tilt 250 EC this week" and blasts a generic Hindi message to 50,000 farmers. The result: a 5% click rate and 95% wasted marketing spend.

**Three root causes, all verifiable from the dataset:**

1. **Wrong timing.** Yellow Rust in Sikar, Rajasthan peaks during the tillering stage (January–February). If you send the campaign in April when harvest is done, the farmer has zero reason to buy. Our analysis of the crop calendar data confirms all 6,000 farmers' precise sowing and harvest dates — timing can be calculated automatically.

2. **Wrong channel.** 25.4% of the 6,000 farmers in the dataset use keypad/feature phones. A WhatsApp message never reaches them. AgriSignal routes keypad farmers to SMS (160 characters) and generates a Voice IVR script for low-literacy farmers — automatically.

3. **No stock, wasted campaign.** The inventory data shows thousands of weekly snapshots with zero stock for certain products in certain districts. AgriSignal checks the latest weekly inventory snapshot and **blocks** any campaign for a product that has fewer than 20 units at local retailers. The budget is not spent marketing something unavailable.

---

## Walkthrough: How to Use the Dashboard

### Step 1: Open the Dashboard
Navigate to `http://localhost:8000/static/index.html`

You will see a three-panel dark-mode interface that loads automatically.

---

### Step 2: Read the Top Navigation Bar

The top bar shows five live numbers computed from the actual dataset:

| Metric | What It Means |
|---|---|
| **Critical Zones** | Districts where priority score ≥ 68 |
| **High Zones** | Districts where priority score ≥ 50 |
| **At-Risk Farmers** | Total farmers in CRITICAL+HIGH districts |
| **WhatsApp** | Number of smartphone farmers who can receive rich WhatsApp content |
| **SMS** | Number of keypad farmers who will receive the compressed SMS version |

The live clock in the top-right confirms data is being computed against today's real date.

---

### Step 3: Read the Risk Queue (Left Panel)

The left panel shows all 33 districts from the dataset, sorted from highest to lowest priority score.

Each card shows:
- **District name and state**
- **Urgency badge** — CRITICAL / HIGH / MEDIUM / LOW
- **Crop and growth stage** — derived from each farmer's crop calendar JSON
- **Live weather** — temperature and humidity fetched from Open-Meteo in real time
- **Three numbers** — farmers at risk, WhatsApp reach, SMS reach
- **Score bar** — visual representation of the priority score

**The urgency classification is season-aware.** In May 2026, all Rabi crops (wheat, chickpea, mustard) have been harvested. The system correctly identifies this as the **Kharif Preparation Window** — a real marketing moment when Syngenta sells soil preparation products, pre-emergence herbicides, and seed treatments before the next season's sowing begins in June–July.

> A CRITICAL badge during an active crop season means a fungal disease window is open and a treatment is needed in the next few days. A HIGH badge during kharif-prep means the farmer segment is highly receptive to pre-season product messaging.

---

### Step 4: Read the Map (Center Panel)

The center panel shows India's map with a colored circle for each district:

| Color | Urgency |
|---|---|
| 🔴 Red | CRITICAL |
| 🟠 Orange | HIGH |
| 🟡 Yellow | MEDIUM |
| 🔵 Blue | LOW |

The **size** of each circle reflects the priority score — a larger circle means more urgency. Clicking a circle selects that district in the right panel and flies the map to that location.

---

### Step 5: Select a District

Click any district card on the left, or click a map circle. The right panel loads:

**District Summary Panel:**
- Crop, growth stage, pest threat, recommended product
- Live weather (temperature + humidity)
- Days to harvest (or days since harvest for kharif-prep)
- Inventory status from latest weekly snapshot
- Language of the dominant farmer segment

**Score Breakdown Grid:** Shows exactly how the priority score was calculated:
- Stage Urgency (40%) — biological risk of the active pest at this growth stage
- Weather Risk (30%) — derived from live humidity and temperature
- Engagement History (20%) — actual historical open rate from the campaign CSV
- Inventory Score (10%) — 0.9 if stock is sufficient, 0.4 if low

**Optimal Send Window:** Day-of-week and time of day derived from historical `message_sent_date` data — which day historically had the best open rates for this state/language.

**Format Receptivity:** Whether this segment responds better to WhatsApp vs SMS, based on device type distribution in the data.

**Channel Breakdown:** Exact counts of how many WhatsApp messages, SMS messages, and Voice IVR calls this campaign would dispatch.

---

### Step 6: Generate the Campaign

Click the green **"Generate Multi-Channel Campaign"** button.

The system:
1. Checks inventory — if low, shows a block message with a retailer restock alert
2. Sends a structured prompt to **Gemini 2.5 Flash** with all the district context
3. Returns a JSON with 6 outputs:

**WhatsApp Message**
A rich vernacular message in the dominant language (Hindi, Punjabi, Gujarati, Kannada, etc.) with a specific ROI calculation — how much the farmer loses without treatment vs. how little the product costs.

**AI Campaign Image**
A photorealistic image generated by **Pollinations.ai** (free, no API key) using a structured template prompt that specifies the state and crop (e.g., "Photorealistic Indian farmer in Gujarat examining wheat field..."). This ensures consistent visual style and high-quality outputs. The image loads in 5–10 seconds.

**SMS — 160 Characters**
A compressed version of the message for keypad phone users. The character counter confirms it is within the 160-character SMS limit.

**Voice / IVR Script**
A 20-second conversational script in the local language for a field representative to read, or to play as an automated robocall to low-literacy farmers who cannot read.

**AI Timing Recommendation**
An AI-generated sentence explaining the optimal time to dispatch this specific campaign based on the historical data pattern.

**Retailer Restock Alert**
A professional English sentence generated for the district retailer, warning them of incoming demand for the recommended product from the at-risk farmer segment.

---

## What Makes This Technically Different

### 1. It is Season-Aware
Most campaign tools send messages regardless of whether the crop is in the ground. AgriSignal reads the actual sowing and harvest dates from each farmer's crop calendar JSON and determines their exact growth stage today. A campaign for Yellow Rust is never generated in May when wheat was harvested in April.

### 2. It is Biologically Calibrated
Fungal diseases (Yellow Rust, Blast, White Rust) require high humidity to spread. If a district shows 12% relative humidity (as North India does in May), our system scores fungal disease risk near-zero — because no fungus can spread in a desert. This is the correct biological answer and can be defended to any agronomy expert.

### 3. It Solves the Offline Farmer Problem Properly
Previous approaches assumed farmers would forward WhatsApp messages to their keypad-using neighbors (a socially naive assumption). AgriSignal eliminates the middleman by generating a parallel SMS campaign for keypad farmers and a Voice IVR script for low-literacy farmers — all from the same button click.

### 4. It Protects Marketing Budget via Inventory Gating
If the recommended product has fewer than 20 units at local retailers (from the weekly snapshot data), the campaign is blocked automatically. Money is never spent creating demand that cannot be fulfilled.

### 5. Every Number is Traceable
The priority score is not a black-box ML output. Every component is a labeled formula with traceable inputs:
- Stage risk → ICAR crop protection guidelines
- Weather risk → Open-Meteo live API + biological literature thresholds
- Engagement history → actual open rates from the provided campaign CSV
- Inventory → the provided weekly inventory CSV

---

## Detailed Breakdown: How We Classify, Score, and Sort

AgriSignal does not use opaque AI or black-box ML to score farmers. It uses a deterministic, rule-based engine built directly into `engine.py`. Here is exactly how every classification is made:

### 1. Crop Window Classification (Seasonality)
We read `sowing.start` and `harvest.end` dates from each farmer's `grower_crop_calendar` JSON. We compare these to **today's date**:
*   **`active`**: Today is between the sowing and harvest dates. (Urgency multiplier: 1.0, or 0.85/0.35 if very close to harvest).
*   **`kharif-prep`**: Today is 0 to 75 days *after* the harvest date. This represents a real marketing window for soil prep and pre-emergence products. (Urgency multiplier: 0.65).
*   **`pre-sowing`**: Today is within 30 days *before* the sowing date starts. Prime window for seed treatments. (Urgency multiplier: 0.70).
*   **`off-season`**: Any other time. These farmers are filtered entirely out of the active campaign queue. (Urgency multiplier: 0.0).

### 2. Biology-Accurate Weather Risk Classification
Fungal diseases (like Rust or Blight) and many pests are heavily dependent on humidity and temperature. We fetch live data from the Open-Meteo API for each district's coordinates.
*   **Humidity Rules**:
    *   `>= 80% RH`: Critical fungal risk (Base score: 0.95)
    *   `>= 70% RH`: High fungal risk (Base score: 0.75)
    *   `>= 60% RH`: Moderate fungal risk (Base score: 0.50)
    *   `>= 50% RH`: Low fungal risk (Base score: 0.25)
    *   `< 50% RH`: Minimal risk (Base score: 0.05) - *Fungus cannot spread in dry air.*
*   **Temperature Modifiers**: Fungi thrive between 15-25°C (multiplies risk by 1.2). Extreme heat > 35°C suppresses fungi (multiplies risk by 0.5). Rain adds +0.12.

### 3. The Campaign Priority Score Formula
Every district is assigned a Priority Score (0-100) using a weighted formula:
```text
Raw Score = 
  (Stage Risk × 0.40)      ← From ICAR pest guidelines (e.g., Wheat Tillering = 0.85)
+ (Weather Risk × 0.30)    ← Live weather score (explained above)
+ (Historical Eng. × 0.20) ← Average open_rate from whatsapp_campaign.csv
+ (Inventory Score × 0.10) ← 0.9 if stock > 20 units, else 0.4

Priority Score = (Raw Score × Seasonal Urgency Multiplier) × 100
```

### 4. Urgency Band Classification
The calculated Priority Score maps to a color-coded urgency band. Crucially, the thresholds change based on the crop season:
*   **Active Crops (Standard Thresholds):**
    *   `>= 68`: **CRITICAL** (Red)
    *   `>= 50`: **HIGH** (Orange)
    *   `>= 33`: **MEDIUM** (Yellow)
    *   `< 33`: **LOW** (Blue)
*   **Kharif-Prep / Pre-Sowing Context (Recalibrated Thresholds):**
    *   Since there is no immediate disease threat, a score of 30 is actually quite good for selling pre-season products.
    *   `>= 28`: **HIGH**
    *   `>= 18`: **MEDIUM**
    *   `< 18`: **LOW**

### 5. Sorting the Queue
The Risk Queue on the left panel of the dashboard is populated by sorting all processed districts in **descending order by Priority Score** (`sorted(results, key=lambda x: -x["priority_score"])`). This ensures the marketing team always sees the most urgent, highest-ROI opportunities at the top.

### 6. Channel & Format Classification
We classify which channel a farmer receives based on their `device_type` from `growers.csv`:
*   `smartphone`: Receives the **WhatsApp (rich image)** campaign.
*   `keypad` or `feature phone`: Receives the **SMS (160-character)** campaign.
*   `low literacy proxy`: We approximate that a fraction of keypad users require voice outreach, so we generate a **Voice IVR Script** for field reps.

---

## Running the Application

```
# From the kisanpulse folder:
python main.py
```

Then open: `http://localhost:8000/static/index.html`

The server takes 3–4 minutes to start because it fetches live weather for all 33 districts from Open-Meteo on startup.

**API Endpoints (for technical demo):**
- `GET /api/risk-zones` — all district risk data
- `GET /api/stats` — aggregated dashboard numbers
- `GET /api/retailer-alerts` — restock alerts for low-stock high-urgency districts
- `POST /api/generate-campaign` — generates multi-channel campaign for a district

---

## Cost to Run

Every component is free:

| Component | Tool | Cost |
|---|---|---|
| Backend | Python + FastAPI | Free |
| Weather data | Open-Meteo API | Free |
| AI content | Gemini 2.5 Flash (free tier) | Free |
| AI images | Pollinations.ai | Free |
| Maps | Leaflet.js + CartoDB | Free |

**Total: ₹0 to run. ₹0 to scale from 6,000 to 6,000,000 farmers.**
