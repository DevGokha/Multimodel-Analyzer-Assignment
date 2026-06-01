from fastapi import FastAPI, File, UploadFile, Form, Response, HTTPException, Request
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

# Constants and Executor
MAX_TEXT_LENGTH = 10000
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp", "image/tiff"}
executor = ThreadPoolExecutor(max_workers=4)

app = FastAPI()

# Add rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter



origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://multimodel-analyzer-assignment.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


import re

def extract_ocr_tags(text: str) -> List[str]:
    if not text:
        return []
    
    safety_triggers = {"toxic", "hate", "idiot", "stupid", "garbage", "bad", "abuse", "scam"}
    business_entities = {"invoice", "billing", "amount", "payment", "price", "card", "charge", "product", "support", "tech", "smartwatch", "device"}
    
    words = re.findall(r'\b\w+\b', text.lower())
    tags = []
    
    for word in words:
        if word in safety_triggers and f"⚠️ {word}" not in tags:
            tags.append(f"⚠️ {word}")
        elif word in business_entities and f"🏷️ {word}" not in tags:
            tags.append(f"🏷️ {word}")
            
    uppercase_words = re.findall(r'\b[A-Z]{3,}\b', text)
    for word in uppercase_words:
        if f"🔍 {word}" not in tags:
            tags.append(f"🔍 {word}")
            
    return tags[:6]


class ImageResult(BaseModel):
    filename: str = "Image file name."
    image_classification: str = "Predicted image category label."
    ocr_text: str = "Text extracted from image (OCR)."
    ocr_tags: List[str] = []


class TopicScore(BaseModel):
    label: str = "Topic label"
    score: float = "Classification confidence score"


class AnalysisResponse(BaseModel):
    text_sentiment: str = "Sentiment label and confidence (e.g. 'POSITIVE (0.95)')."
    text_summary: str = "Summary of the input text."
    topic_classification: str = "Predicted topic label."
    image_classification: str = "Predicted label for the first image."
    ocr_text: str = "OCR text from the first image."
    toxicity_warning: str = "Toxicity warning message."
    automated_response: str = "Automated system response."
    image_results: List[ImageResult] = []
    topic_scores: List[TopicScore] = []


@app.get("/", summary="Health check", description="Returns a status message.", response_description="API status message.")
def read_root():
    return {"message": "Multimodal Analyzer API is running!"}


@app.post("/analyze", response_model=AnalysisResponse, summary="Analyze text and images", description="Analyzes text and images for sentiment, summary, topic, image classification, OCR, and toxicity.", response_description="Analysis results.")
@limiter.limit("5/minute")
async def analyze_data(
    request: Request,
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

    # Step 3e: Process all images concurrently using parallel grouping
    try:
        cls_tasks = [
            loop.run_in_executor(executor, analyzer.classify_image, img_data["bytes"])
            for img_data in image_data_list
        ]
        cls_raw_results = await asyncio.gather(*cls_tasks)
    except Exception as e:
        logger.error(f"Concurrent image classification failed: {e}")
        cls_raw_results = ["Classification failed"] * len(image_data_list)

    try:
        ocr_tasks = [
            loop.run_in_executor(executor, analyzer.extract_text_from_image, img_data["bytes"])
            for img_data in image_data_list
        ]
        ocr_raw_results = await asyncio.gather(*ocr_tasks)
    except Exception as e:
        logger.error(f"Concurrent image OCR failed: {e}")
        ocr_raw_results = [""] * len(image_data_list)

    image_results = []
    all_ocr_texts = []
    for idx, img_data in enumerate(image_data_list):
        cls_result = cls_raw_results[idx]
        ocr_result = ocr_raw_results[idx]
        extracted_text = str(ocr_result) if not isinstance(ocr_result, Exception) else ""
        classification = str(cls_result) if not isinstance(cls_result, Exception) else "Classification failed"
        tags = extract_ocr_tags(extracted_text)
        
        image_results.append(ImageResult(
            filename=img_data["filename"] or "image",
            image_classification=classification.split(',')[0],
            ocr_text=extracted_text,
            ocr_tags=tags,
        ))
        all_ocr_texts.append(extracted_text)

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
    if isinstance(topic_result, dict):
        top_topic = topic_result["labels"][0]
        topic_scores = [TopicScore(label=l, score=s) for l, s in zip(topic_result["labels"], topic_result["scores"])]
    else:
        top_topic = topic_result
        topic_scores = [TopicScore(label=topic_result, score=1.0)]

    response = AnalysisResponse(
        text_sentiment=f"{sentiment_result['label']} ({sentiment_result['score']:.2f})",
        text_summary=summary_result,
        topic_classification=top_topic,
        image_classification=image_results[0].image_classification if image_results else "N/A",
        ocr_text=image_results[0].ocr_text if image_results else "",
        toxicity_warning=toxicity_warning,
        automated_response=automated_response,
        image_results=image_results,
        topic_scores=topic_scores,
    )

    return response

@app.post("/analyze-stream", summary="Analyze text and images with real-time stream", description="Streams real-time progress updates and returns final analysis results.")
@limiter.limit("5/minute")
async def analyze_stream(
    request: Request,
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

    async def stream_generator():
        loop = asyncio.get_event_loop()
        import json

        # Step 0: Uploading data...
        yield f"data: {json.dumps({'status': 'processing', 'step': 0, 'message': 'Uploading data...'})}\n\n"
        await asyncio.sleep(0.1)

        # Step 1: Analyzing sentiment...
        yield f"data: {json.dumps({'status': 'processing', 'step': 1, 'message': 'Analyzing sentiment...'})}\n\n"
        try:
            sentiment_result = await loop.run_in_executor(executor, analyzer.analyze_sentiment, text)
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            yield f"data: {json.dumps({'status': 'error', 'detail': 'Sentiment analysis failed.'})}\n\n"
            return

        # Step 2: Summarizing text...
        yield f"data: {json.dumps({'status': 'processing', 'step': 2, 'message': 'Summarizing text...'})}\n\n"
        try:
            summary_result = await loop.run_in_executor(executor, analyzer.summarize_text, text)
        except Exception as e:
            logger.error(f"Text summarization failed: {e}")
            yield f"data: {json.dumps({'status': 'error', 'detail': 'Text summarization failed.'})}\n\n"
            return

        # Step 3: Classifying topic...
        yield f"data: {json.dumps({'status': 'processing', 'step': 3, 'message': 'Classifying topic...'})}\n\n"
        try:
            if topic_labels:
                topic_result = await loop.run_in_executor(executor, analyzer.classify_topic, text, topic_labels)
            else:
                topic_result = await loop.run_in_executor(executor, analyzer.classify_topic, text)
        except Exception as e:
            logger.error(f"Topic classification failed: {e}")
            yield f"data: {json.dumps({'status': 'error', 'detail': 'Topic classification failed.'})}\n\n"
            return

        # Step 4: Checking toxicity...
        yield f"data: {json.dumps({'status': 'processing', 'step': 4, 'message': 'Checking toxicity...'})}\n\n"
        try:
            text_toxicity_result = await loop.run_in_executor(executor, analyzer.check_toxicity, text)
        except Exception as e:
            logger.error(f"Text toxicity check failed: {e}")
            yield f"data: {json.dumps({'status': 'error', 'detail': 'Toxicity check failed on input text.'})}\n\n"
            return

        # Step 5: Classifying images...
        yield f"data: {json.dumps({'status': 'processing', 'step': 5, 'message': 'Classifying images...'})}\n\n"
        try:
            cls_tasks = [
                loop.run_in_executor(executor, analyzer.classify_image, img_data["bytes"])
                for img_data in image_data_list
            ]
            cls_raw_results = await asyncio.gather(*cls_tasks)
        except Exception as e:
            logger.error(f"Concurrent image classification failed: {e}")
            cls_raw_results = ["Classification failed"] * len(image_data_list)

        # Step 6: Extracting text from images (OCR)...
        yield f"data: {json.dumps({'status': 'processing', 'step': 6, 'message': 'Extracting text from images (OCR)...'})}\n\n"
        try:
            ocr_tasks = [
                loop.run_in_executor(executor, analyzer.extract_text_from_image, img_data["bytes"])
                for img_data in image_data_list
            ]
            ocr_raw_results = await asyncio.gather(*ocr_tasks)
        except Exception as e:
            logger.error(f"Concurrent image OCR failed: {e}")
            ocr_raw_results = [""] * len(image_data_list)

        final_image_results = []
        all_ocr_texts = []
        for idx, img_data in enumerate(image_data_list):
            cls_result = cls_raw_results[idx]
            ocr_result = ocr_raw_results[idx]
            extracted_text = str(ocr_result) if not isinstance(ocr_result, Exception) else ""
            classification = str(cls_result) if not isinstance(cls_result, Exception) else "Classification failed"
            tags = extract_ocr_tags(extracted_text)
            
            final_image_results.append(ImageResult(
                filename=img_data["filename"] or "image",
                image_classification=classification.split(',')[0],
                ocr_text=extracted_text,
                ocr_tags=tags,
            ))
            all_ocr_texts.append(extracted_text)

        # Step 7: Generating response...
        yield f"data: {json.dumps({'status': 'processing', 'step': 7, 'message': 'Generating response...'})}\n\n"
        try:
            combined_ocr = " ".join(all_ocr_texts)
            ocr_toxicity_result = await loop.run_in_executor(executor, analyzer.check_toxicity, combined_ocr)
        except Exception as e:
            logger.error(f"OCR toxicity check failed: {e}")
            yield f"data: {json.dumps({'status': 'error', 'detail': 'Toxicity check failed on extracted image text.'})}\n\n"
            return

        primary_class = final_image_results[0].image_classification if final_image_results else ""
        nlp_data = {"sentiment": sentiment_result, "toxicity": text_toxicity_result}
        cv_data = {"classification": primary_class, "ocr_toxicity": ocr_toxicity_result}
        automated_response = analyzer.generate_automated_response(nlp_data, cv_data)

        toxicity_warning = "None"
        if text_toxicity_result['is_toxic'] and ocr_toxicity_result['is_toxic']:
            toxicity_warning = "Toxicity detected in both text and image."
        elif text_toxicity_result['is_toxic']:
            toxicity_warning = "Toxicity detected in input text."
        elif ocr_toxicity_result['is_toxic']:
            toxicity_warning = "Toxicity detected in image text (OCR)."

        # Return full response
        if isinstance(topic_result, dict):
            top_topic = topic_result["labels"][0]
            topic_scores = [{"label": l, "score": s} for l, s in zip(topic_result["labels"], topic_result["scores"])]
        else:
            top_topic = topic_result
            topic_scores = [{"label": topic_result, "score": 1.0}]

        response_payload = {
            "text_sentiment": f"{sentiment_result['label']} ({sentiment_result['score']:.2f})",
            "text_summary": summary_result,
            "topic_classification": top_topic,
            "image_classification": final_image_results[0].image_classification if final_image_results else "N/A",
            "ocr_text": final_image_results[0].ocr_text if final_image_results else "",
            "toxicity_warning": toxicity_warning,
            "automated_response": automated_response,
            "image_results": [img.model_dump() for img in final_image_results],
            "topic_scores": topic_scores,
        }
        yield f"data: {json.dumps({'status': 'completed', 'results': response_payload})}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

@app.post("/generate-report", summary="Generate PDF report", description="Generates a branded PDF report from analysis results.", response_description="PDF file.")
async def generate_report(analysis_data: AnalysisResponse):
    """
    Accepts analysis JSON and returns a PDF report.
    """
    # Step 8: Wrap PDF generation in error handling
    try:
        pdf_bytes = pdf_generator.create_report(analysis_data.model_dump())
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