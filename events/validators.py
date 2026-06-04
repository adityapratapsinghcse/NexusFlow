from django.core.exceptions import ValidationError

ALLOWED_DOC_TYPES = ['application/pdf','image/jpeg','image/png','image/webp']
ALLOWED_IMAGE_TYPES = ['image/jpeg','image/png','image/webp','image/gif']
MAX_MB = 5

def validate_document(file):
    if file.size > MAX_MB * 1024 * 1024:
        raise ValidationError(f"File must be under {MAX_MB}MB.")
    ct = getattr(file, 'content_type', '')
    if ct and ct not in ALLOWED_DOC_TYPES:
        raise ValidationError("Only PDF and image files are allowed.")

def validate_image(file):
    if file.size > MAX_MB * 1024 * 1024:
        raise ValidationError(f"Image must be under {MAX_MB}MB.")
    ct = getattr(file, 'content_type', '')
    if ct and ct not in ALLOWED_IMAGE_TYPES:
        raise ValidationError("Only JPEG, PNG, WebP, GIF images are allowed.")