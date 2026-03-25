from fastapi import FastAPI, File, UploadFile, Form, Response, HTTPException
from fastapi.responses import StreamingResponse 
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
from typing import List, Optional
import logging
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
import analyzer
import pdf_generator
from dotenv import load_dotenv
from slowapi import Limiter
from slowapi.util import get_remote_address

# Load environment variables from .env
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Add rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

app = FastAPI()


origins = [
    "http://localhost:3000",
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


class ImageResult(BaseModel):
    filename: str = "Image file name."
    image_classification: str = "Predicted image category label."
    ocr_text: str = "Text extracted from image (OCR)."


class AnalysisResponse(BaseModel):
    text_sentiment: str = "Sentiment label and confidence (e.g. 'POSITIVE (0.95)')."
    text_summary: str = "Summary of the input text."
    topic_classification: str = "Predicted topic label."
    image_classification: str = "Predicted label for the first image."
    ocr_text: str = "OCR text from the first image."
    toxicity_warning: str = "Toxicity warning message."
    automated_response: str = "Automated system response."
    image_results: List[ImageResult] = []


@app.get("/", summary="Health check", description="Returns a status message.", response_description="API status message.")
def read_root():
    return {"message": "Multimodal Analyzer API is running!"}


@app.post("/analyze", response_model=AnalysisResponse, summary="Analyze text and images", description="Analyzes text and images for sentiment, summary, topic, image classification, OCR, and toxicity.", response_description="Analysis results.")
@limiter.limit("5/minute")
async def analyze_data(
    text: str = Form(..., description="Text to analyze (max 10,000 chars)"),
    images: List[UploadFile] = File(..., description="One or more image files (JPEG, PNG, GIF, WebP, BMP, TIFF; max 10MB each)"),
    topics: Optional[str] = Form(None, description="Comma-separated custom topic labels for classification"),
):
    # Step 1b: Validate text length — reject if too long to prevent memory issues
    if len(text) > MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Text is too long. Maximum allowed length is {MAX_TEXT_LENGTH} characters (you sent {len(text)})."
        )

    # Step 2: Read and validate all uploaded images
    image_data_list = []
    for img in images:
        # Step 2a: Validate each image's MIME type
        if img.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type '{img.content_type}' for '{img.filename}'. Allowed: JPEG, PNG, GIF, WebP, BMP, TIFF."
            )
        # Step 2b: Read image bytes with error handling
        try:
            img_bytes = await img.read()
        except Exception as e:
            logger.error(f"Failed to read image '{img.filename}': {e}")
            raise HTTPException(status_code=400, detail=f"Failed to read image '{img.filename}'.")
        # Step 2c: Validate file size
        if len(img_bytes) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"Image '{img.filename}' is too large. Maximum allowed size is {MAX_FILE_SIZE_MB}MB."
            )
        image_data_list.append({"filename": img.filename or "image", "bytes": img_bytes})

    # Step 2d: Parse custom topic labels if the user provided them (comma-separated)
    topic_labels = None
    if topics and topics.strip():
        topic_labels = [t.strip() for t in topics.split(',') if t.strip()]

    # Step 3: Run analysis tasks sequentially to prevent out-of-memory crashes.
    # Loading multiple large models at once can exceed available system memory,
    # so we run them one-by-one through a single-worker thread pool.
    loop = asyncio.get_event_loop()

    # Step 3a: Sentiment analysis
    try:
        sentiment_result = await loop.run_in_executor(executor, analyzer.analyze_sentiment, text)
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Sentiment analysis failed. The model may be unavailable or out of memory.")

    # Step 3b: Text summarization
    try:
        summary_result = await loop.run_in_executor(executor, analyzer.summarize_text, text)
    except Exception as e:
        logger.error(f"Text summarization failed: {e}")
        raise HTTPException(status_code=500, detail="Text summarization failed. The model may be unavailable or out of memory.")

    # Step 3c: Topic classification (with optional custom labels)
    try:
        if topic_labels:
            topic_result = await loop.run_in_executor(executor, analyzer.classify_topic, text, topic_labels)
        else:
            topic_result = await loop.run_in_executor(executor, analyzer.classify_topic, text)
    except Exception as e:
        logger.error(f"Topic classification failed: {e}")
        raise HTTPException(status_code=500, detail="Topic classification failed. The model may be unavailable or out of memory.")

    # Step 3d: Toxicity check on input text
    try:
        text_toxicity_result = await loop.run_in_executor(executor, analyzer.check_toxicity, text)
    except Exception as e:
        logger.error(f"Text toxicity check failed: {e}")
        raise HTTPException(status_code=500, detail="Toxicity check failed on input text.")

    # Step 3e: Process each image sequentially — classify then OCR
    image_results = []
    all_ocr_texts = []
    for img_data in image_data_list:
        try:
            cls_result = await loop.run_in_executor(executor, analyzer.classify_image, img_data["bytes"])
        except Exception as e:
            logger.error(f"Image classification failed for {img_data['filename']}: {e}")
            cls_result = "Classification failed"
        try:
            ocr_result = await loop.run_in_executor(executor, analyzer.extract_text_from_image, img_data["bytes"])
        except Exception as e:
            logger.error(f"OCR failed for {img_data['filename']}: {e}")
            ocr_result = ""
        image_results.append(ImageResult(
            filename=img_data["filename"] or "image",
            image_classification=cls_result.split(',')[0] if isinstance(cls_result, str) else str(cls_result),
            ocr_text=ocr_result,
        ))
        all_ocr_texts.append(ocr_result)

    # Step 4: Run OCR toxicity check on combined OCR text from all images
    combined_ocr = " ".join(all_ocr_texts)
    try:
        ocr_toxicity_result = await loop.run_in_executor(executor, analyzer.check_toxicity, combined_ocr)
    except Exception as e:
        logger.error(f"OCR toxicity check failed: {e}")
        raise HTTPException(status_code=500, detail="Toxicity check failed on extracted image text.")

    # Step 5: Generate automated response from combined results
    primary_class = image_results[0].image_classification if image_results else ""
    nlp_data = {"sentiment": sentiment_result, "toxicity": text_toxicity_result}
    cv_data = {"classification": primary_class, "ocr_toxicity": ocr_toxicity_result}
    automated_response = analyzer.generate_automated_response(nlp_data, cv_data)

    # Step 6: Determine toxicity warning message
    toxicity_warning = "None"
    if text_toxicity_result['is_toxic'] and ocr_toxicity_result['is_toxic']:
        toxicity_warning = "Toxicity detected in both text and image."
    elif text_toxicity_result['is_toxic']:
        toxicity_warning = "Toxicity detected in input text."
    elif ocr_toxicity_result['is_toxic']:
        toxicity_warning = "Toxicity detected in image text (OCR)."

    # Step 7: Build and return the response (primary fields use first image for backward compat)
    response = AnalysisResponse(
        text_sentiment=f"{sentiment_result['label']} ({sentiment_result['score']:.2f})",
        text_summary=summary_result,
        topic_classification=topic_result,
        image_classification=image_results[0].image_classification if image_results else "N/A",
        ocr_text=image_results[0].ocr_text if image_results else "",
        toxicity_warning=toxicity_warning,
        automated_response=automated_response,
        image_results=image_results,
    )

    return response

@app.post("/generate-report", summary="Generate PDF report", description="Generates a branded PDF report from analysis results.", response_description="PDF file.")
async def generate_report(analysis_data: AnalysisResponse):
    """
    Accepts analysis JSON and returns a PDF report.
    """
    # Step 8: Wrap PDF generation in error handling
    try:
        pdf_bytes = pdf_generator.create_report(analysis_data.dict())
    except Exception as e:
        logger.error(f"PDF report generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate the PDF report. Please try again.")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=analysis_report.pdf"}
    )

if __name__ == "__main__":
    # Step 9: Read the port from the PORT environment variable, defaulting to 8000
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)