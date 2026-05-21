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
        data["raw_image_url"] = pollinations_url
        
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


# ── Call Dispatch Endpoint ───────────────────────────────────────────────────
class CallRequest(BaseModel):
    phone_numbers: list[str]
    message: str
    language: str

@app.post("/api/dispatch/call")
def dispatch_calls(req: CallRequest):
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
    auth_token  = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
    from_number = os.environ.get("TWILIO_FROM_NUMBER", "").strip()
    
    if not account_sid or not auth_token or not from_number:
        return {
            "status": "simulated",
            "message": "Twilio credentials missing in .env. Simulating call in browser..."
        }
        
    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        
        # Map languages to Twilio's standard Polly TTS voices (avoid premium -Neural suffix for compatibility)
        # Check if text is Hinglish / Latin script vs Regional script
        import re
        import html
        
        escaped_message = html.escape(req.message)
        is_latin = not bool(re.search(r'[^\x00-\x7F]', req.message))
        
        if is_latin:
            lang_code = "en-IN"
            voice_name = "Polly.Raveena" # Standard Indian English voice
        else:
            voice_map = {
                "Hindi": ("hi-IN", "Polly.Aditi"),
                "Gujarati": ("gu-IN", "alice"),
                "Marathi": ("mr-IN", "Polly.Aditi"),  # Fallback to Hindi Devnagari for Marathi
                "Tamil": ("ta-IN", "alice"),
                "Telugu": ("te-IN", "alice"),
                "Kannada": ("kn-IN", "alice"),
                "Punjabi": ("pa-IN", "alice"),
                "Bengali": ("bn-IN", "alice")
            }
            lang_code, voice_name = voice_map.get(req.language, ("hi-IN", "Polly.Aditi"))
        
        voice_attr = f'voice="{voice_name}"' if voice_name != "standard" else ""
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?><Response><Say language="{lang_code}" {voice_attr}>{escaped_message}</Say></Response>"""
        
        call_ids = []
        for phone in req.phone_numbers:
            # clean number: ensure country code is present
            clean_phone = phone.replace("+", "").replace(" ", "").strip()
            if not clean_phone:
                continue
            if len(clean_phone) == 10:
                clean_phone = "+91" + clean_phone
            elif not clean_phone.startswith("+"):
                clean_phone = "+" + clean_phone
                
            call = client.calls.create(
                to=clean_phone,
                from_=from_number,
                twiml=twiml
            )
            call_ids.append(call.sid)
            
        return {
            "status": "real",
            "message": f"Successfully placed {len(call_ids)} outbound call(s)!",
            "call_ids": call_ids
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Twilio API Error: {str(e)}"
        }


# ── SMS Dispatch Endpoint ────────────────────────────────────────────────────
class SmsRequest(BaseModel):
    phone_numbers: list[str]
    message: str

@app.post("/api/dispatch/sms")
def dispatch_sms(req: SmsRequest):
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
    auth_token  = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
    from_number = os.environ.get("TWILIO_FROM_NUMBER", "").strip()
    
    if not account_sid or not auth_token or not from_number:
        return {
            "status": "simulated",
            "message": "Twilio credentials missing in .env. Simulating SMS dispatch..."
        }
        
    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        
        message_sids = []
        for phone in req.phone_numbers:
            clean_phone = phone.replace("+", "").replace(" ", "").strip()
            if not clean_phone:
                continue
            if len(clean_phone) == 10:
                clean_phone = "+91" + clean_phone
            elif not clean_phone.startswith("+"):
                clean_phone = "+" + clean_phone
                
            msg = client.messages.create(
                to=clean_phone,
                from_=from_number,
                body=req.message
            )
            message_sids.append(msg.sid)
            
        return {
            "status": "real",
            "message": f"Successfully sent {len(message_sids)} SMS via Twilio!",
            "message_sids": message_sids
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Twilio SMS Error: {str(e)}"
        }


# ── WhatsApp Dispatch Endpoint ───────────────────────────────────────────────
class WhatsappRequest(BaseModel):
    phone_numbers: list[str]
    message: str
    image_url: str | None = None

@app.post("/api/dispatch/whatsapp")
def dispatch_whatsapp(req: WhatsappRequest):
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
    auth_token  = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
    
    # Use dedicated TWILIO_WHATSAPP_FROM_NUMBER if set, otherwise default to Twilio Sandbox number '+14155238886'
    wa_from_raw = os.environ.get("TWILIO_WHATSAPP_FROM_NUMBER", "").strip()
    if not wa_from_raw:
        wa_from_raw = "+14155238886"
        
    if not account_sid or not auth_token:
        return {
            "status": "simulated",
            "message": "Twilio credentials missing in .env. Simulating WhatsApp dispatch..."
        }
        
    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        
        # Prepend 'whatsapp:' if not already present
        clean_from = wa_from_raw.replace("whatsapp:", "").strip()
        wa_from = f"whatsapp:{clean_from}"
        
        message_sids = []
        for phone in req.phone_numbers:
            clean_phone = phone.replace("+", "").replace(" ", "").strip()
            if not clean_phone:
                continue
            if len(clean_phone) == 10:
                clean_phone = "+91" + clean_phone
            elif not clean_phone.startswith("+"):
                clean_phone = "+" + clean_phone
                
            wa_to = f"whatsapp:{clean_phone}"
            
            params = {
                "to": wa_to,
                "from_": wa_from,
                "body": req.message
            }
            if req.image_url:
                params["media_url"] = [req.image_url]
                
            msg = client.messages.create(**params)
            message_sids.append(msg.sid)
            
        return {
            "status": "real",
            "message": f"Successfully sent {len(message_sids)} WhatsApp message(s) via Twilio!",
            "message_sids": message_sids
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Twilio WhatsApp Error: {str(e)}"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
