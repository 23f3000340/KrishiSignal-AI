"""
AgriSignal — FastAPI Backend
Multi-channel campaign orchestration API.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import google.generativeai as genai
import os, json, urllib.parse, random
from dotenv import load_dotenv
from engine import AgriSignalEngine

load_dotenv()
app = FastAPI(title="AgriSignal API")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

from fastapi.responses import HTMLResponse

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
# Create static directory dynamically if missing to prevent FastAPI crash
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
@app.get("/static/index.html")
def serve_index():
    # Try inside static folder first, then fallback to root
    for path in [os.path.join(STATIC_DIR, "index.html"), os.path.join(os.path.dirname(__file__), "index.html"), "index.html"]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
    raise HTTPException(status_code=404, detail="index.html not found")

# ── Startup: pre-compute risk zones (expensive — do once) ─────────────────────
print("Computing risk zones...")
engine     = AgriSignalEngine()
RISK_ZONES = engine.compute_risk_zones()
print(f"Risk zones ready: {len(RISK_ZONES)} districts processed.")

api_key = os.environ.get("GEMINI_API_KEY", "").strip().replace("\r", "").replace("\n", "")
if api_key:
    genai.configure(api_key=api_key)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/api/risk-zones")
def get_risk_zones(min_urgency: str = "LOW", limit: int = 50):
    ORDER = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    min_val = ORDER.get(min_urgency, 1)
    filtered = [z for z in RISK_ZONES if ORDER.get(z["urgency"], 0) >= min_val]
    return filtered[:limit]


@app.get("/api/retailer-alerts")
def get_retailer_alerts():
    return engine.get_retailer_alerts(RISK_ZONES)


@app.get("/api/stats")
def get_stats():
    critical = sum(1 for z in RISK_ZONES if z["urgency"] == "CRITICAL")
    high     = sum(1 for z in RISK_ZONES if z["urgency"] == "HIGH")
    total_farmers = sum(z["farmers_total"] for z in RISK_ZONES)
    at_risk       = sum(z["farmers_atrisk"] for z in RISK_ZONES)
    whatsapp      = sum(z["channels"]["whatsapp"] for z in RISK_ZONES)
    sms           = sum(z["channels"]["sms"] for z in RISK_ZONES)
    avg_score     = sum(z["priority_score"] for z in RISK_ZONES) / len(RISK_ZONES) if RISK_ZONES else 0
    return {
        "critical_districts": critical,
        "high_districts":     high,
        "total_farmers":      total_farmers,
        "farmers_at_risk":    at_risk,
        "whatsapp_reach":     whatsapp,
        "sms_reach":          sms,
        "avg_priority_score": round(avg_score, 1)
    }


class CampaignRequest(BaseModel):
    district: str


@app.post("/api/generate-campaign")
async def generate_campaign(req: CampaignRequest):
    zone = next((z for z in RISK_ZONES if z["district"] == req.district), None)
    if not zone:
        raise HTTPException(status_code=404, detail="District not found")

    if not api_key:
        return {"blocked": True, "reason": "GEMINI_API_KEY not set in .env file"}

    lang        = zone["dominant_language"]
    crop        = zone["crop"]
    stage       = zone["growth_stage"]
    pest        = zone["pest"]
    sku         = zone["sku"]
    district    = zone["district"]
    state       = zone["state"]
    wx          = zone["weather"]
    days        = zone["days_to_harvest"]
    at_risk     = zone["farmers_atrisk"]
    opt_time    = zone.get("optimal_send_time", "Tuesday–Thursday, 6–8 AM")
    fmt_rec     = zone.get("format_receptivity", {})
    breakdown   = zone.get("score_breakdown", {})
    inventory   = zone["inventory"]["units"]
    recent_sales = zone["inventory"].get("recent_sales", 0)

    prompt = f"""
You are AgriSignal, Syngenta India's precision campaign AI.

FARMER SEGMENT CONTEXT:
- Location: {district}, {state}
- Crop: {crop} | Growth Stage: {stage} | Days to Harvest: {days}
- Active Biological Threat: {pest} (HIGH RISK this week)
- Weather: {wx['temp']}°C, Humidity {wx['humidity']}%, Rain: {wx['rain']}mm
- Recommended Product: {sku}
- Inventory Status: {inventory} units available ({"LOW STOCK SCARCITY MARKETING NEEDED" if not zone["inventory"]["sufficient"] else "Stock verified at local retailers"})
- Farmers at risk in this zone: {at_risk}
- Primary Language: {lang}
- Historically best send time: {opt_time}
- Most effective channel for this segment: {fmt_rec.get('primary_channel','WhatsApp')}
- Historical campaign open rate: {fmt_rec.get('dataset_open_rate','N/A')}

Your task: Generate a precision multi-channel campaign package.
Return ONLY a valid JSON object with these exact keys:

1. "whatsapp_text": Rich {lang} WhatsApp message. Include specific ROI: cost of {sku} vs yield saved per acre. Max 300 chars. Urgent, human, peer-trusted tone.{" IMPORTANT: Stock is critically low. Explicitly tell the farmer to rush and book the product before it sells out!" if not zone["inventory"]["sufficient"] else ""}
2. "sms_text": Compressed {lang} SMS STRICTLY UNDER 130 characters. Must include product name and one clear action step.{" Add urgency that stock is running out." if not zone["inventory"]["sufficient"] else ""}
3. "voice_script": 20-second IVR script in {lang} for field rep robocall. Simple, no jargon, one clear action.{" Warn them that local stock is almost gone." if not zone["inventory"]["sufficient"] else ""}
4. "image_prompt": One-sentence photorealistic image description in English. Indian farmer in {state} examining {crop} crop showing {pest} damage. Under 80 words. No text, logos, or words in image.
5. "retailer_alert": One professional English sentence alerting the {district} retailer of incoming demand for {sku} from {at_risk} at-risk farmers. Cite that there are {inventory} units in stock and {recent_sales} units were sold recently to highlight urgency.
6. "send_recommendation": One English sentence stating the optimal day and time to send this campaign and why.

Output ONLY the JSON. No explanation, no markdown fences.
"""
    try:
        model    = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.4,
            )
        )
        text = response.text.strip()
        data = json.loads(text)

        # Build Pollinations image URL using a simplified prompt to prevent API errors
        img_prompt = f"Photorealistic Indian farmer in {state} examining {crop} field, clear sky, highly detailed"
        encoded    = urllib.parse.quote(img_prompt, safe="")
        seed       = random.randint(1, 999999)
        pollinations_url = f"https://image.pollinations.ai/prompt/{encoded}?model=turbo&width=900&height=450&nologo=true&seed={seed}"
        
        # Fetch and base64 encode on the server side to bypass client-side adblockers/VPN blocks
        b64_img = None
        try:
            import httpx
            import base64
            with httpx.Client(timeout=8.0) as client:
                img_res = client.get(pollinations_url)
                if img_res.status_code == 200:
                    b64_data = base64.b64encode(img_res.content).decode("utf-8")
                    b64_img = f"data:image/jpeg;base64,{b64_data}"
                    # Cache the successful image on disk
                    cache_path = os.path.join(STATIC_DIR, "cached_campaign.jpg")
                    with open(cache_path, "wb") as f:
                        f.write(img_res.content)
        except Exception as e:
            print(f"Server-side image generation failed: {e}")
            
        if not b64_img:
            # Fallback 1: Try to load cached image from disk
            cache_path = os.path.join(STATIC_DIR, "cached_campaign.jpg")
            if os.path.exists(cache_path):
                import base64
                with open(cache_path, "rb") as f:
                    b64_data = base64.b64encode(f.read()).decode("utf-8")
                    b64_img = f"data:image/jpeg;base64,{b64_data}"
            else:
                # Fallback 2: If no cache exists, use a highly reliable Unsplash URL
                b64_img = "https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=900&h=450&fit=crop&q=80"
                
        data["image_url"] = b64_img
        
        # Enforce SMS length strictly
        sms = data.get("sms_text", "")
        if len(sms) > 160:
            sms = sms[:157] + "..."
        data["sms_text"] = sms

        return {
            "zone":     zone,
            "campaign": data
        }
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"AI returned invalid JSON: {str(e)[:200]}")
    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg or "Quota" in err_msg:
            raise HTTPException(status_code=429, detail="Gemini Free Tier limit reached. Please wait 60 seconds before generating the next campaign.")
        raise HTTPException(status_code=500, detail=f"Gemini API error: {err_msg[:300]}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
