# 🌾 KisanPulse: The Farmer Trust Network
*Syngenta Hackathon 2026 - AI-Powered Agricultural Marketing at Scale*

## 1. The Problem Statement & Industry Reality

**The Core Problem:**
Syngenta’s current agricultural marketing treats farmers like consumers of FMCG products (broadcast model). However, smallholder farmers are rational investors making critical capital allocation decisions under severe biological time pressure and economic risk. 

**Data-Backed Realities (Extracted from Syngenta Datasets):**
1. **Low Conversion:** Generic WhatsApp campaigns have only a 5% click-through rate.
2. **The "Invisible" 25%:** 1,521 out of 6,000 farmers (25.4%) in the data use keypad phones or have unknown devices. They are completely excluded from digital WhatsApp campaigns.
3. **Wasted Spend on Stockouts:** Our analysis found 9,348 stockout events (3% of inventory weeks). Campaigns are currently recommending products (e.g., Tilt 250 EC) to farmers whose nearest retailer has zero stock.
4. **Ignored Trust Networks:** Farmers don't buy because a corporation texts them; they buy because a trusted neighboring farmer recommends it.

---

## 2. The Solution: KisanPulse

**Concept:**
Instead of broadcasting generic messages from "Syngenta" to millions of farmers, KisanPulse identifies existing **Key Opinion Leaders (KOLs)** in every village and turns them into AI-empowered local advisors. 

We don't send campaigns TO farmers. We turn our most engaged farmers INTO the campaign.
If 1 KOL influences 50 neighbors, engaging just the 3,922 KOLs in our data gives Syngenta a potential reach of ~196,000 farmers organically, including the 25% who only have keypad phones.

### The Three Pillars of KisanPulse:

#### A. The KOL Identification Engine
Systematically finds the most influential farmers (KOLs) using existing behavioral data, rather than surveys.
*   **Metrics Used:** Offline campaign attendance (demonstrated engagement), product scan history, farm size, and early-adopter purchase behavior.

#### B. Crop ROI Radar (Economic Urgency)
Farmers don't buy "fungicide"; they buy "risk mitigation". 
*   Instead of saying "Buy Tilt 250 EC to fight rust", the system calculates real-time economics: *"Your wheat is at tillering stage. Yellow Rust risk is HIGH this week. Protecting it costs ₹480/acre but saves ₹9,120/acre in yield loss. Window closes in 8 days."*

#### C. Kisan Vaani (WhatsApp AI Copilot for KOLs)
A WhatsApp-based AI assistant specifically for KOLs. When a neighbor asks a KOL for advice, the KOL forwards a photo/question to Kisan Vaani. The AI returns a highly localized, vernacular advisory containing the ROI calculation and the *nearest retailer with verified stock*. The KOL then forwards this trusted advice to their village WhatsApp group.

---

## 3. Technical Architecture & Implementation

KisanPulse is a full-stack, AI-driven intelligence loop built entirely on free-tier, highly scalable tools.

### A. Data Fusion Layer
*   **Internal Data:** `growers.csv` (crop calendar, language, device), `retailer_pos.csv` (pricing, buying patterns), `retailer_inventory_weekly.csv` (stock availability), `whatsapp_campaign.csv` (engagement history).
*   **External APIs (Free):** 
    *   **Open-Meteo API:** Real-time weather data to assess pest/disease risk.
    *   **ICAR/Agmarknet:** Baseline crop yield loss data and Mandi prices for ROI calculations.

### B. Intelligence Core (Machine Learning & Logic)
1.  **KOL Scoring Algorithm (Deterministic):** Ranks 6,000 growers by influence potential.
    *   `Score = (0.3*offline_attended) + (0.25*product_scans) + (0.2*farm_size_percentile) + (0.15*early_adopter) + (0.1*tehsil_activity)`
2.  **Campaign Engagement Propensity (XGBoost):**
    *   **Features:** Language, device type, crop stage at send, weather risk, local stock availability, KOL proximity.
    *   **Target:** `clicked_status` (Actual conversion intent).
    *   **Outcome:** Predicts which farmers are most likely to convert, raising baseline CTR from 5% to a predicted 15-18%.
3.  **Dynamic Inventory Gating:** A hard rule engine that blocks any campaign generation if the recommended product has < 10 units at the target farmer's nearest retailer.

### C. Content Generation Layer (Generative AI)
*   **Model:** Google Gemini 1.5 Flash API (Fast, 1M free tokens/day).
*   **Function:** Generates hyper-personalized messages in 6 vernacular languages (Hindi, Punjabi, Marathi, Gujarati, Kannada, Bengali).
*   **Adaptation:** Formats as rich WhatsApp cards for smartphones, and compressed 160-character SMS summaries for keypad users.

### D. Presentation & Delivery (Frontend)
*   **Tech Stack:** FastAPI (Python backend), HTML/Vanilla JS/Leaflet.js (Frontend Dashboard).
*   **Dashboard Features:** 
    *   Heatmap of KOL density and district-level biological urgency.
    *   Live Campaign Generator showing localized message previews.
    *   "Field Copilot" view for Syngenta Reps, showing the top 3 high-priority farmers to visit daily based on urgency and inventory.

---

## 4. Expected Business Impact (For the Presentation)

| Metric | Current Baseline | KisanPulse Projection |
| :--- | :--- | :--- |
| **Click-Through Rate** | 5% | **15-20%** (via Propensity Targeting & ROI framing) |
| **Campaign Reach** | Linear (Cost per farmer) | **Exponential** (1 KOL reaches ~50 neighbors organically) |
| **Non-Smartphone Reach**| 0 (Excluded) | **~100% of village** via Word-of-Mouth |
| **Wasted Ad Spend** | High (Due to Stockouts) | **Zero** (Inventory-gated messaging) |
| **Content Variants** | ~10 generic variants | **3,000+** micro-targeted variants (Auto-generated) |

---

## 5. Why This Idea Wins
1. **Respects Rural Psychology:** Leverages peer-to-peer trust networks instead of trying to replace them with corporate broadcasting.
2. **Deep Data Utilization:** We found the hidden "25% invisible farmers" and the "3% stockout waste" in the datasets provided, proving deep analytical rigor.
3. **Economic Centricity:** Shifts the marketing narrative from "Product Features" to "Financial ROI," which is exactly how smallholders make purchasing decisions.
4. **Ready to Scale:** The architecture uses production-ready ML (XGBoost) and GenAI (Gemini) that can immediately pilot in one state and scale nationally with near-zero marginal content creation costs.
