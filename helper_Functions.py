# helper_Functions.py
import pgeocode

_nom = pgeocode.Nominatim('us')

def zip_to_state(zip_code):
    """
    Map a US ZIP code (string) to a 2-letter state code using pgeocode.
    If lookup fails, return None.
    """
    try:
        if not zip_code or zip_code.strip() == "":
            return None
        # pgeocode expects 5-digit zips; sometimes dataset has 'XXXXX-XXXX' or lacking leading zeros
        z = str(zip_code).split("-")[0].zfill(5)[:5]
        res = _nom.query_postal_code(z)
        state_code = res.state_code if hasattr(res, "state_code") else res['state_code'] if 'state_code' in res else None
        # If state_code is nan or empty, return None
        if state_code is None or (isinstance(state_code, float) and pd.isna(state_code)):
            return None
        return state_code
    except Exception:
        return None
