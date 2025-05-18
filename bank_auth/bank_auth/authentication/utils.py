import random
import string
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import send_mail
import cv2
import numpy as np
import pytesseract
from PIL import Image
import io

def generate_otp(length=6):
    """Generate a random OTP with specified length"""
    return ''.join(random.choices(string.digits, k=length))

def calculate_otp_expiry():
    """Calculate OTP expiry time based on settings"""
    return datetime.now() + timedelta(minutes=settings.OTP_EXPIRY_TIME)

def send_otp_email(email, otp):
    """Send OTP via email"""
    subject = 'Your Bank App Verification Code'
    message = f'Your verification code is: {otp}\n\nThis code will expire in {settings.OTP_EXPIRY_TIME} minutes.'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]
    
    try:
        send_mail(subject, message, from_email, recipient_list)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def extract_id_text(image_file):
    """Extract text from ID image using OCR"""
    try:
        # Read image file
        image = Image.open(image_file)
        image_np = np.array(image)
        
        # Convert to grayscale and apply preprocessing
        gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        
        # Perform OCR
        text = pytesseract.image_to_string(gray)
        return text
    except Exception as e:
        print(f"Error processing image: {e}")
        return ""

def validate_id_document(front_image, back_image, id_number):
    
    # Extract text from both images
    front_text = extract_id_text(front_image)
    back_text = extract_id_text(back_image)
    
    # Simple validation: check if ID number appears in OCR text
    # In a real system, more sophisticated validation would be needed
    if id_number in front_text or id_number in back_text:
        return True, "ID successfully validated"
    
    return False, "Could not verify ID number on provided documents"
