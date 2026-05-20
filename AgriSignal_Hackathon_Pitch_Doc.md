# 🌾 AgriSignal — Technical Slide Document & System Architecture
### *Autonomous Agricultural Risk Scoring & Contextual Marketing Orchestrator*
**Deployment Link:** [huggingface.co/spaces/Sarthak5628/agrisignal](https://huggingface.co/spaces/Sarthak5628/agrisignal)

---

## Slide 1: System Vision & Command Center UI

AgriSignal is a precision agricultural marketing command center. It replaces traditional mass broadcasts with context-aware, multi-channel campaigns driven by real-time crop biology, local weather conditions, and inventory availability.

```text
+-----------------------------------------------------------------------------------+
|  AGRISIGNAL COMMAND CENTER UI                                                     |
+-----------------------------------+-----------------------------------------------+
| PANEL 1: RISK QUEUE (Left)        | PANEL 3: CAMPAIGN GENERATOR (Right)            |
| Sorted by Priority Score (0-100)  | - District Context Summary                    |
| Shows: District, Crop, Stage, RH  | - Priority Score Breakdown Grid               |
+-----------------------------------+ - Channel Reach Segment Breakdown             |
| PANEL 2: INTERACTIVE MAP (Center) | - Dynamic Campaign Output:                    |
| Leaflet.js Map with Urgency-Color |   * Vernacular WhatsApp Copy + Base64 Visual  |
| and Score-Sized Circular Markers  |   * Truncated SMS copy + Voice IVR script     |
+-----------------------------------+-----------------------------------------------+
```

### Production Tech Stack:
*   **Backend:** Python 3.10 with FastAPI (asynchronous ASGI framework).
*   **Frontend:** Single-page app using HTML5, Custom Dark-Mode CSS, and Leaflet.js maps.
*   **AI Engine:** Google Gemini 2.5 Flash API (text copy) and Pollinations Turbo (base64 image streaming).

---

## Slide 2: Problem Interpretation — Broadcast vs. Precision Campaigning

Traditional crop input marketing treats farmers as generic FMCG consumers. This ignores the biological time windows, climate factors, and supply chain constraints of farming.

```text
[Broadcast Campaign]  -----> Blasts product ads blindly -----> 5% CTR & high stockout frustration
[Precision Campaign]  -----> Syncs biology, stock & channel -----> 15-18% CTR & zero stockout waste
```

### The Three Operational Failures:
1.  **Temporal Mismatch:** Campaigns are sent regardless of crop growth stage or weather. (e.g. promoting rust fungicide post-harvest or during dry spells).
2.  **Hardware Exclusion:** 25.4% of farmers in our dataset use keypad/feature phones and cannot receive rich WhatsApp content.
3.  **Inventory Mismatch:** Weekly inventory data shows frequent local stockouts. Broadcasting campaigns for out-of-stock products wastes ad spend and frustrates farmers.

---

## Slide 3: Data Schema & Fusion Logic

We parsed and fused five local CSV datasets and a live weather API to assess real-time risk without assumptions:

```text
  growers.csv ------------------+
  retailers.csv ----------------+---> [AgriSignal Fusion Engine] ---> Priority Sorted Queue
  retailer_inventory_weekly.csv +       (Linked via District)
  whatsapp_campaign.csv --------+
  retailer_pos.csv -------------+
```

### Extracted Data Schemas:
*   **`growers.csv`:** Extracted `district`, `state`, `crop`, `language`, `device_type`, `grower_crop_calendar` (JSON string containing sowing/harvest dates), and `opened_rate`.
*   **`retailers.csv`:** Extracted name and coordinates (`latitude`, `longitude`) to map local dealerships.
*   **`retailer_inventory_weekly.csv`:** Extracted weekly SKU levels to check local product stock.
*   **`whatsapp_campaign.csv`:** Extracted message dispatch timestamps and click statuses to calculate optimal send times and channel preferences.
*   **`retailer_pos.csv`:** Extracted sales quantity to highlight recent sales velocity in retail warnings.

---

## Slide 4: System Architecture & Execution Sequence

```text
[FastAPI Backend Startup]
    |--> os.makedirs("static") (Prevents Starlette mount errors)
    |--> Parse CSV Datasets into memory (Pandas DataFrames)
    |--> Compute District Risk Queue (Open-Meteo weather caching)
          |
          +--> [Front-End Page Load] (Serves index.html from root/static)
                |--> Fetch /api/risk-zones (Populates map & risk cards)
                |--> User selects a District card (Triggers Right Panel load)
                |--> User clicks "Generate Campaign" (Triggers POST /api/generate-campaign)
                      |--> Enforce Inventory Gate (Stock check)
                      |--> Call Gemini 2.5 Flash API (json_mode, temperature=0.4)
                      |--> Call Pollinations Turbo (Server-side Base64 image cache)
                      |--> Stream Campaign Package back to UI
```

### Server-Side Image Caching:
To bypass client-side VPN blocks, adblockers, and CORS errors, the backend server downloads the campaign graphic, encodes it to **Base64** (`data:image/jpeg;base64,...`), and caches a local copy at `static/cached_campaign.jpg` as a fallback.

---

## Slide 5: The Priority Scoring Algorithm

Each district is scored dynamically to ensure complete transparency for field operators:

$$\text{Priority Score } (P) = \min\left(100, 100 \times \left[ \text{StageRisk} \times 0.40 + \text{WeatherRisk} \times 0.30 + \text{EngageScore} \times 0.20 + \text{StockScore} \times 0.10 \right]\right)$$

### 1. Weights & Inputs:
*   **Stage Risk ($S_r$):** Biological crop vulnerability (e.g. wheat tillering = 0.85; flowering = 0.75; vegetative = 0.50).
*   **Weather Risk ($W_r$):** Humidity and temperature pathogen suitability (Slide 6).
*   **Engagement Score ($E_h$):** Average historical campaign click rate for the district segment.
*   **Stock Score ($I_s$):** Enforces a low-stock penalty (scored as 0.9 if local stock $\ge 10$ units, else 0.4).

### 2. Statistical Confidence Margin:
The engine computes a 95% confidence interval margin using the standard error of the score to account for sample size ($n$) variances:

$$\text{Margin} = \max\left(2.0, \min\left(15.0, 1.96 \times \sqrt{\frac{P \times (100 - P)}{n}}\right)\right)$$

---

## Slide 6: Biology-Aware Weather Risk Classifier

Pathogenic agricultural fungi (like Rusts or Blights) require specific microclimates to spread. The backend engine implements a deterministic rule classifier:

```text
                    [Open-Meteo Live Weather Query]
                                   |
                  +----------------+----------------+
                  |                                 |
           [RH >= 50%]                         [RH < 50%]
                  |                                 |
     Apply Humidity Risk Scale              Weather Risk = 0.05
    (RH 80%+=0.95, RH 70%+=0.75,            (Fungus inactive in
     RH 60%+=0.50, RH 50%+=0.25)                dry air)
                  |
         [Apply Temp Modifiers]
    (Optimal 15-25C: multiply by 1.2)
    (Extreme >35C  : multiply by 0.5)
                  |
           [Apply Rain Mod]
        (Rain > 0: add +0.12)
                  |
             [Cap at 1.0]
```

*   **Dry-Air Suppression:** If relative humidity is $< 50\%$, the risk score drops to $0.05$. This prevents the system from generating false disease alarms in dry environments.

---

## Slide 7: Multi-Channel Device Routing & Truncation

The system automatically splits campaign delivery based on the hardware profiles in the district:

```text
                         [District Grower Segment]
                                     |
                       +-------------+-------------+
                       |                           |
                 [Smartphones]              [Keypad Phones]
                 (Device == 'smartphone')    (Device == 'keypad'/'unknown')
                       |                           |
                 WhatsApp Route                 SMS Route
              (Rich Vernacular text       (Plain Vernacular text
               + Base64 AI Visual)         strictly <= 130 chars)
                                                   |
                                             Voice IVR Route
                                         (Conversational script
                                           for low literacy)
```

### Vernacular Language Engine:
Campaigns are generated in the district's dominant language (Hindi, Punjabi, Marathi, Gujarati, Kannada, Bengali) based on the mode value in the dataset.

---

## Slide 8: Operations — Inventory Gating & B2B Alerts

To prevent ad waste and customer frustration, AgriSignal implements strict inventory gating before campaign dispatch:

```text
Campaign Generation Requested for District D
   |
   +--> Query local inventory for recommended SKU
         |
         +--> Inventory >= 10 units?
               |
               +--> YES: Proceed to Gemini Campaign Generation
               |
               +--> NO : BLOCK Campaign + Generate B2B Retailer Restock Alert
```

### The Retailer Restock Alert Schema:
```json
{
  "district": "Mehsana",
  "sku": "Tilt 250 EC",
  "current_stock": 9,
  "farmers_at_risk": 82,
  "alert_message": "Mehsana Retailer Alert: 82 farmers are at risk of Karnal Bunt this week. Your stock is only 9 units. Expect incoming demand; please book restock immediately."
}
```

This alert routes directly to the supply chain team to coordinate restocks before demand peaks.

---

## Slide 9: Expected Impact & Measurement Plan

We measure success across biological, operational, and customer engagement dimensions:

| Dimension | Metric | Measurement Method | Expected Impact |
| :--- | :--- | :--- | :--- |
| **Engagement** | Campaign CTR | Track links clicked vs. total messages dispatched. | **15.0% - 18.0%** (up from 5% baseline) |
| **Operational**| Wasted Ad-Spend | Ratio of campaigns sent to regions with stocked-out products. | **0.0%** (via automated inventory gating) |
| **Reach** | Demographics | Count of active responses from SMS & IVR channels. | **+25.4%** coverage of offline keypad phone segment |
| **Business** | Sell-Through | POS transaction logs mapped to campaign timing. | Correlation of local sales velocity with campaign dispatch |

---

## Slide 10: Assumptions & Real-World Limitations

*   **POS Sync Latency:** The system assumes weekly inventory updates. Real-world deployments require real-time ERP/POS data connectors to prevent out-of-stock lags.
*   **Weather Resolution:** Open-Meteo coordinates are district-level. Microclimates in valleys or hillsides are not captured.
*   **Offline Conversion Tracking:** Keypad-phone conversion tracking relies on digital coupon codes or scanning QR codes on the physical bottles at POS.
*   **Static Sowing Calendars:** Sowing windows are parsed from historical grower profiles. Monsoonal shifts can alter crop stages, requiring satellite vegetation index inputs (like NDVIs) to update stages dynamically in future iterations.
