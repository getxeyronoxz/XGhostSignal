import phonenumbers
from phonenumbers import geocoder, carrier

PLUGIN_NAME = "phone_intel_basic"
VERSION = "1.0.0"

def run(number: str, region: str = None) -> dict:
    """
    Analyzes a phone number to extract extended intelligence (carrier and location)
    using the core phonenumbers library.
    """
    try:
        parsed = phonenumbers.parse(number, region)
        if not phonenumbers.is_valid_number(parsed):
            return {"status": "error", "message": "Invalid number"}

        loc = geocoder.description_for_number(parsed, "en")
        car = carrier.name_for_number(parsed, "en")
        
        return {
            "status": "success",
            "country_code": parsed.country_code,
            "national_number": parsed.national_number,
            "location_guess": loc,
            "carrier_guess": car,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
