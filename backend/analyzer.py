from transformers import pipeline
from PIL import Image
import easyocr
from profanity_check import predict_prob
import gc
import threading


# Step 1: Use load-use-unload pattern to keep only one model in memory at a time.
# This prevents out-of-memory crashes on systems with limited RAM/page file.

# Step 1a: Store each model reference (None when not loaded)
sentiment_analyzer = None
summarizer = None
topic_classifier = None
image_classifier = None
ocr_reader = None

# Step 1b: Lock to prevent race conditions when loading/unloading models
_model_lock = threading.Lock()


def _unload_all_except(keep=None):
    """Step 1c: Unload all models except the one we're about to use.
    This ensures only one large model is in memory at any time, preventing OOM crashes."""
    global sentiment_analyzer, summarizer, topic_classifier, image_classifier, ocr_reader
    if keep != "sentiment" and sentiment_analyzer is not None:
        sentiment_analyzer = None
    if keep != "summarizer" and summarizer is not None:
        summarizer = None
    if keep != "topic" and topic_classifier is not None:
        topic_classifier = None
    if keep != "image" and image_classifier is not None:
        image_classifier = None
    if keep != "ocr" and ocr_reader is not None:
        ocr_reader = None
    gc.collect()


def analyze_sentiment(text: str):
    """Step 2: Load sentiment model, run inference, then unload it to free memory.
    Only POSITIVE or NEGATIVE labels are returned by this distilbert model."""
    global sentiment_analyzer
    with _model_lock:
        # Step 2a: Unload all other models before loading this one
        _unload_all_except("sentiment")
        # Step 2b: Load model if not already loaded
        if sentiment_analyzer is None:
            print("Loading sentiment model...")
            sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
        # Step 2c: Run inference
        result = sentiment_analyzer(text)[0]
        # Step 2d: Unload model immediately after use to free memory
        print("Unloading sentiment model...")
        sentiment_analyzer = None
        gc.collect()
    return {"label": result['label'], "score": result['score']}


def summarize_text(text: str):
    """Step 3: Load summarization model, run inference, then unload it."""
    global summarizer
    if len(text.split()) <= 40:
        return "Text is too short to summarize."
    with _model_lock:
        # Step 3a: Unload all other models before loading this one
        _unload_all_except("summarizer")
        # Step 3b: Load model if not already loaded
        if summarizer is None:
            print("Loading summarization model...")
            summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-6-6")
        # Step 3c: Run inference
        result = summarizer(text, max_length=50, min_length=20, do_sample=False)
        # Step 3d: Unload model immediately after use to free memory
        print("Unloading summarization model...")
        summarizer = None
        gc.collect()
    return result[0]['summary_text']


def classify_topic(text: str, topics=None):
    """Step 4: Load zero-shot topic classifier, run inference, then unload it.
    Uses distilled BART-MNLI (~300MB) instead of the full model (~1.6GB)."""
    if topics is None:
        topics = ["news", "review", "comment", "complaint"]
    global topic_classifier
    with _model_lock:
        # Step 4a: Unload all other models before loading this one
        _unload_all_except("topic")
        # Step 4b: Load model if not already loaded
        if topic_classifier is None:
            print("Loading topic classification model...")
            topic_classifier = pipeline("zero-shot-classification", model="valhalla/distilbart-mnli-12-3")
        # Step 4c: Run inference
        result = topic_classifier(text, candidate_labels=topics)
        # Step 4d: Unload model immediately after use to free memory
        print("Unloading topic classification model...")
        topic_classifier = None
        gc.collect()
    return result['labels'][0]


def classify_image(image_bytes: bytes):
    """Step 5: Load image classifier, run inference, then unload it."""
    global image_classifier
    from io import BytesIO
    image = Image.open(BytesIO(image_bytes))
    with _model_lock:
        # Step 5a: Unload all other models before loading this one
        _unload_all_except("image")
        # Step 5b: Load model if not already loaded
        if image_classifier is None:
            print("Loading image classification model...")
            image_classifier = pipeline("image-classification", model="google/vit-base-patch16-224")
        # Step 5c: Run inference
        result = image_classifier(image)
        # Step 5d: Unload model immediately after use to free memory
        print("Unloading image classification model...")
        image_classifier = None
        gc.collect()
    return result[0]['label']


def extract_text_from_image(image_bytes: bytes):
    """Step 6: Load OCR reader, extract text, then unload it."""
    global ocr_reader
    with _model_lock:
        # Step 6a: Unload all other models before loading this one
        _unload_all_except("ocr")
        # Step 6b: Load OCR reader if not already loaded
        if ocr_reader is None:
            print("Loading OCR reader...")
            ocr_reader = easyocr.Reader(['en'], gpu=False)
        # Step 6c: Run OCR text extraction
        result = ocr_reader.readtext(image_bytes)
        # Step 6d: Unload OCR reader immediately after use to free memory
        print("Unloading OCR reader...")
        ocr_reader = None
        gc.collect()
    extracted_text = " ".join([item[1] for item in result])
    return extracted_text

def check_toxicity(text: str):
    if not text.strip():
        return {"is_toxic": False, "score": 0.0}
    
    score = predict_prob([text])[0]
    is_toxic = score > 0.6 # Set a threshold
    return {"is_toxic": is_toxic, "score": score}



def generate_automated_response(nlp_results: dict, cv_results: dict):
    sentiment = nlp_results.get('sentiment', {}).get('label', 'NEUTRAL')
    is_toxic_text = nlp_results.get('toxicity', {}).get('is_toxic', False)
    is_toxic_ocr = cv_results.get('ocr_toxicity', {}).get('is_toxic', False)
    image_cat = cv_results.get('classification', '')
    
    if is_toxic_text or is_toxic_ocr:
        return "Warning: Potentially toxic content detected. Your submission will be reviewed by a moderator."

   
    if sentiment == 'NEGATIVE':
        return "We are sorry to hear you had a negative experience. A team member will review your feedback shortly."
        
    if sentiment == 'POSITIVE':
        if 'product' in image_cat.lower():
             return "Thank you for the positive feedback! We're glad you're enjoying the product."
        else:
            return "Thank you for your positive feedback! We appreciate you sharing with us."

    return "Thank you for your feedback. We have received your submission."

