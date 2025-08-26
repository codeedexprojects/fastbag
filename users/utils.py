from django.conf import settings
import requests

def send_otp_2factor(mobile_number, otp):
    api_key = settings.TWO_FACTOR_API_KEY
    url = f"https://2factor.in/API/V1/{api_key}/SMS/{mobile_number}/{otp}"

    response = requests.get(url)
    data = response.json()

    if data.get('Status') == 'Success':
        return True
    else:
        raise Exception(f"Failed to send OTP: {data.get('Details')}")
    

# from rest_framework_simplejwt.tokens import RefreshToken

# def generate_vendor_token(vendor):
#     refresh = RefreshToken()
#     refresh['vendor_id'] = vendor.id  # Add custom claims for vendor-specific data
#     refresh['email'] = vendor.email
#     return {
#         'refresh': str(refresh),
#         'access': str(refresh.access_token),
#     }


from math import radians, sin, cos, sqrt, atan2

def haversine(lat1, lon1, lat2, lon2):

    R = 6371  # Earth radius in KM
    dlat = radians(float(lat2) - float(lat1))
    dlon = radians(float(lon2) - float(lon1))
    a = sin(dlat / 2) ** 2 + cos(radians(float(lat1))) * cos(radians(float(lat2))) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c
