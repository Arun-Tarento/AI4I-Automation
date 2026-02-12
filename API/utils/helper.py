import base64

#audio to srt converter
def audio_to_base64(file_path: str) -> str:
    """Convert audio file to base64"""
    with open(file_path, 'rb') as audio_file:
        return base64.b64encode(audio_file.read()).decode('utf-8')


def image_to_base64(file_path: str) -> str:
    """Convert image file to base64"""
    with open(file_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')