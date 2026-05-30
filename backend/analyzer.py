from transformers import pipeline
from PIL import Image
import easyocr
from profanity_check import predict_prob
import gc
import threading


# Step 1: Use warm-caching with automatic idle-unload (TTL) to keep only one model in memory.
# This prevents out-of-memory crashes on systems with limited RAM, while optimizing latency for subsequent requests.

class WarmModel:
    def __init__(self, name, loader_fn, ttl_seconds=300):
        self.name = name
        self.loader_fn = loader_fn
        self.ttl_seconds = ttl_seconds
        self.model = None
        self.timer = None
        self.lock = threading.Lock()

    def load_and_get(self):
        with self.lock:
            # Cancel any scheduled idle unload timer
            if self.timer is not None:
                self.timer.cancel()
                self.timer = None
            
            # If the model is not currently in memory, unload others first and then load it
            if self.model is None:
                _unload_all_except(self.name)
                print(f"Loading {self.name} model...")
                self.model = self.loader_fn()
            
            return self.model

    def release_after_use(self):
        with self.lock:
            # Cancel existing timer to avoid duplicate schedules
            if self.timer is not None:
                self.timer.cancel()
            
            # Start timer to unload after self.ttl_seconds of inactivity
            self.timer = threading.Timer(self.ttl_seconds, self._unload)
            self.timer.daemon = True  # Ensure timer thread does not block server shutdown
            self.timer.start()
            print(f"Scheduled idle-unload for {self.name} model in {self.ttl_seconds} seconds...")

    def _unload(self):
        with self.lock:
            if self.model is not None:
                print(f"Idle timeout reached. Unloading {self.name} model to free memory...")
                self.model = None
                self.timer = None
                gc.collect()

# Define model loader helper functions
def _load_sentiment():
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

def _load_summarizer():
    return pipeline("summarization", model="sshleifer/distilbart-cnn-6-6")

def _load_topic():
    return pipeline("zero-shot-classification", model="valhalla/distilbart-mnli-12-3")

def _load_image():
    return pipeline("image-classification", model="google/vit-base-patch16-224")

def _load_ocr():
    return easyocr.Reader(['en'], gpu=False)

# Registry of warm model instances (5-minute TTL by default)
models_registry = {
    "sentiment": WarmModel("sentiment", _load_sentiment, ttl_seconds=300),
    "summarizer": WarmModel("summarizer", _load_summarizer, ttl_seconds=300),
    "topic": WarmModel("topic", _load_topic, ttl_seconds=300),
    "image": WarmModel("image", _load_image, ttl_seconds=300),
    "ocr": WarmModel("ocr", _load_ocr, ttl_seconds=300),
}

_model_lock = threading.Lock()

def _unload_all_except(keep=None):
    """Unload all active models in the registry except the specified one to enforce the single-model RAM constraint."""
    for name, warm_model in models_registry.items():
        if name != keep:
            with warm_model.lock:
                if warm_model.timer is not None:
                    warm_model.timer.cancel()
                    warm_model.timer = None
                if warm_model.model is not None:
                    print(f"Force unloading {name} model to load {keep}...")
                    warm_model.model = None
    gc.collect()



def analyze_sentiment(text: str):
    """Step 2: Load sentiment model, run inference, then release/cache it."""
    warm_model = models_registry["sentiment"]
    model = warm_model.load_and_get()
    
    result = model(text, truncation=True)[0]
    
    warm_model.release_after_use()
    return {"label": result['label'], "score": result['score']}


def summarize_text(text: str):
    """Step 3: Load summarization model, run inference, then release/cache it."""
    if len(text.split()) <= 40:
        return "Text is too short to summarize."
    
    warm_model = models_registry["summarizer"]
    model = warm_model.load_and_get()
    
    result = model(text, max_length=50, min_length=20, do_sample=False, truncation=True)
    
    warm_model.release_after_use()
    return result[0]['summary_text']


def classify_topic(text: str, topics=None):
    """Step 4: Load zero-shot topic classifier, run inference, then release/cache it.
    Uses distilled BART-MNLI (~300MB) instead of the full model (~1.6GB)."""
    if topics is None:
        topics = ["news", "review", "comment", "complaint"]
    
    warm_model = models_registry["topic"]
    model = warm_model.load_and_get()
    
    result = model(text, candidate_labels=topics, truncation=True)
    
    warm_model.release_after_use()
    return {"labels": result['labels'], "scores": result['scores']}


def classify_image(image_bytes: bytes):
    """Step 5: Load image classifier, run inference, then release/cache it."""
    from io import BytesIO
    image = Image.open(BytesIO(image_bytes))
    
    warm_model = models_registry["image"]
    model = warm_model.load_and_get()
    
    result = model(image)
    
    warm_model.release_after_use()
    return result[0]['label']


def extract_text_from_image(image_bytes: bytes):
    """Step 6: Load OCR reader, extract text, then release/cache it."""
    warm_model = models_registry["ocr"]
    model = warm_model.load_and_get()
    
    result = model.readtext(image_bytes)
    
    warm_model.release_after_use()
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

