### 2.3 Processing Uploaded Media

After uploading media files, we often need to process them to extract useful information or generate derivatives. Let's explore how we can process different types of media in our Think-Tank project.

#### Image Processing with Pillow in FastAPI

For image processing, we can use the Pillow library in FastAPI. Let's create an endpoint to resize an uploaded image:

```python
# main.py
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from PIL import Image
import io

app = FastAPI()

@app.post("/process-image")
async def process_image(file: UploadFile = File(...)):
    try:
        # Read the uploaded image
        image = Image.open(io.BytesIO(await file.read()))

        # Resize the image
        resized_image = image.resize((300, 300))

        # Save the resized image to a buffer
        buffer = io.BytesIO()
        resized_image.save(buffer, format="JPEG")
        buffer.seek(0)

        # Return the resized image as a file response
        return FileResponse(buffer, media_type="image/jpeg", filename="resized.jpg")
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
```

This endpoint receives an uploaded image, resizes it to 300x300 pixels using Pillow, and returns the resized image as a file response.

#### Video Thumbnail Generation

To generate thumbnails for uploaded videos, we can use the `ffmpeg` library. Here's an example of how you can generate a thumbnail using `ffmpeg` in FastAPI:

```python
# main.py
import subprocess

@app.post("/generate-thumbnail")
async def generate_thumbnail(file: UploadFile = File(...)):
    try:
        # Save the uploaded video to a temporary file
        with open("temp_video.mp4", "wb") as f:
            f.write(await file.read())

        # Generate thumbnail using ffmpeg
        subprocess.run([
            "ffmpeg",
            "-i", "temp_video.mp4",
            "-ss", "00:00:01.000",
            "-vframes", "1",
            "thumbnail.jpg"
        ])

        # Return the generated thumbnail as a file response
        return FileResponse("thumbnail.jpg", media_type="image/jpeg", filename="thumbnail.jpg")
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    finally:
        # Clean up temporary files
        os.remove("temp_video.mp4")
        os.remove("thumbnail.jpg")
```

This endpoint saves the uploaded video to a temporary file, uses `ffmpeg` to generate a thumbnail from the first second of the video, and returns the thumbnail as a file response.

#### Document Text Extraction

To extract text from uploaded documents, we can use libraries like `PyPDF2` for PDF files or `python-docx` for Word documents. Here's an example of how you can extract text from a PDF file:

```python
# main.py
from PyPDF2 import PdfReader

@app.post("/extract-text")
async def extract_text(file: UploadFile = File(...)):
    try:
        # Read the uploaded PDF file
        pdf = PdfReader(io.BytesIO(await file.read()))

        # Extract text from each page
        text = ""
        for page in pdf.pages:
            text += page.extract_text()

        return JSONResponse(content={"text": text})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
```

This endpoint reads the uploaded PDF file using `PdfReader`, extracts text from each page, and returns the extracted text as a JSON response.

#### Metadata Extraction

To extract metadata from uploaded files, we can use libraries like `exifread` for image files or `hachoir-metadata` for various file types. Here's an example of how you can extract metadata from an image file:

```python
# main.py
import exifread

@app.post("/extract-metadata")
async def extract_metadata(file: UploadFile = File(...)):
    try:
        # Read the uploaded image file
        tags = exifread.process_file(io.BytesIO(await file.read()))

        # Extract relevant metadata
        metadata = {
            "camera": tags.get("Image Make", ""),
            "model": tags.get("Image Model", ""),
            "date": tags.get("Image DateTime", ""),
            # Add more metadata fields as needed
        }

        return JSONResponse(content={"metadata": metadata})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
```

This endpoint reads the uploaded image file using `exifread`, extracts relevant metadata fields, and returns the metadata as a JSON response.

By processing uploaded media, we can extract valuable information, generate derivatives, and enhance the functionality of our Think-Tank project.