from django.shortcuts import render
from django.contrib import messages
from .models import QRCode
import qrcode
from django.core.files.storage import FileSystemStorage
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from pathlib import Path
from pyzbar.pyzbar import decode
from PIL import Image


def generate_qr(request):
    qr_image_url = None

    if request.method == 'POST':
        data = request.POST.get('data')
        mobile = request.POST.get('mobile')

        if not data and mobile or len(mobile) != 10:
            messages.error(request, "Invalid Mobile Number or Data field is empty!")
            return render(request, 'scanner/generate.html')

        try:
            qr_content = f"{data}|{mobile}"
            qr = qrcode.make(qr_content) # Generate QR code image using 'qrcode' library
            qr_image_io = BytesIO() # Create in-memory file to store image temporarily
            qr.save(qr_image_io, format='PNG') # Save QR image into in-memory file as PNG
            qr_image_io.seek(0)  # Reset file pointer to beginning
            qr_storage_path = settings.MEDIA_ROOT / 'qr_codes' # Define folder where QR images will be stored
            fs = FileSystemStorage(location=qr_storage_path, base_url="/media/qr_codes/") # Initialize FileSystemStorage for this folder
            filename = f"{data}_{mobile}.png" # Create a unique filename using data and mobile
            qr_image_content = ContentFile(qr_image_io.read(), name=filename) # Wrap in-memory image bytes into a ContentFile (for saving)
            file_name = fs.save(filename, qr_image_content) # Save file to disk under /media/qr_codes/
            qr_image_url = fs.url(filename) # Get the public URL to access the QR image

            QRCode.objects.create(data=data, mobile_number=mobile) # Save record in database (QRCode model stores data + mobile)

            messages.success(request, "QR Code generated successfully!")
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")

    return render(request, 'scanner/generate.html', {'qr_image_url': qr_image_url})


def scan_qr(request):
    decoded_data = None

    if request.method == 'POST' and request.FILES.get('qr_image'):
        qr_image = request.FILES['qr_image']
        mobile = request.POST.get('mobile')

        if not mobile or len(mobile) != 10:
            messages.error(request, "Invalid mobile number.")
            return render(request, 'scanner/scanner.html')

        try:
            # Open image directly from uploaded file (no saving to disk)
            image = Image.open(qr_image) # Pillow (PIL) can open an in-memory file object directly
            decoded_objects = decode(image) # Decode the image using pyzbar

            # Check if any QR code was detected
            if decoded_objects:
                qr_content = decoded_objects[0].data.decode('utf-8').strip() # Get the data from the first detected QR code
                parts = qr_content.split('|')  # Expecting QR content in format: "data|mobile"

                if len(parts) == 2:
                    qr_data, qr_mobile = parts
                    qr_entry = QRCode.objects.filter(data=qr_data, mobile_number=qr_mobile).first() # Search for this QR code entry in the database

                    # Verify if QR code exists and matches mobile number
                    if qr_entry and qr_mobile == mobile:
                        messages.success(request, f"QR valid! Data: {qr_data}")
                        decoded_data = qr_data
                        qr_entry.delete()
                    else:
                        messages.error(request, "Invalid or mismatched QR code.")
                else:
                    messages.error(request, "Invalid QR code format.")
            else:
                messages.error(request, "No QR code found in the image.")

        except Exception as e:
            messages.error(request, f"Error scanning QR: {str(e)}")

    return render(request, 'scanner/scanner.html', {'decoded_data': decoded_data})
