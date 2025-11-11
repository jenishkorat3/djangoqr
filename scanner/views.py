from django.shortcuts import render


def generate_qr(request):
    return render(request, 'scanner/generate.html')


def scan_qr(request):
    return render(request, 'scanner/scanner.html')
