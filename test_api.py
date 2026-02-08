import google.generativeai as genai
import os
from dotenv import load_dotenv
import time

load_dotenv()

# ១. ដាក់ API Key របស់អ្នក (ដែលអ្នកបានផ្ញើមកមុននេះ)
# ⚠️ បម្រាម៖ ក្រោយពេលតេស្តចប់ សូមចូលទៅលុប Key នេះចោល ហើយបង្កើតថ្មី ដើម្បីសុវត្ថិភាព!
api_key = os.environ.get('GEMINI_API_KEY') or "AIzaSyCoZOlO1-2hsYx2wBZtZvVlQTlO3FCGWL0"

genai.configure(api_key=api_key)

# ២. បញ្ជីឈ្មោះ Model ដែលយើងនឹងសាកល្បង (តាមលំដាប់)
models_to_try = [
    'gemini-flash-latest',       # ជម្រើសទី ១ (Free & Fast)
    'gemini-pro-latest',         # ជម្រើសទី ២ (Free & Smart)
    'gemini-pro',                # ជម្រើសទី ៣ (Old Stable)
    'gemini-2.0-flash-lite-preview-09-2025', # ជម្រើសទី ៤ (New Lite)
    'gemini-1.5-flash-latest'    # ជម្រើសទី ៥
]

print(f"🔍 កំពុងស្វែងរក Model ដែលដំណើរការសម្រាប់គណនីរបស់អ្នក...\n")

success_model = None

for model_name in models_to_try:
    print(f"👉 កំពុងសាកល្បង: {model_name} ... ", end="")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say Hello in Khmer")
        
        print("✅ ជោគជ័យ!")
        print(f"\n🎉 រកឃើញហើយ! ឈ្មោះ Model ដែលត្រូវប្រើគឺ៖ \"{model_name}\"")
        print(f"💬 ចម្លើយពី AI: {response.text}")
        success_model = model_name
        break # ឈប់ស្វែងរក ព្រោះរកឃើញហើយ
        
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            print("❌ (រកឈ្មោះមិនឃើញ)")
        elif "429" in error_msg:
            print("⏳ (អស់ Quota - រង់ចាំបន្តិច)")
        else:
            print(f"❌ (Error: {e})")
    
    time.sleep(1) # សម្រាក ១ វិនាទីសិន

if success_model:
    print("\n" + "="*50)
    print(f"✅ សូមយកឈ្មោះនេះទៅដាក់ក្នុង app.py របស់អ្នក៖")
    print(f"   model = genai.GenerativeModel('{success_model}')")
    print("="*50)
else:
    print("\n😭 សុំទោស! មិនមាន Model ណាមួយដំណើរការទេ។ សូមឆែកមើល Billing ក្នុង Google AI Studio។")