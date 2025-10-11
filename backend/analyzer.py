from transformers import pipeline
from PIL import Image
import easyocr
from profanity_check import predict_prob

sentiment_analyzer = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")

summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
topic_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")


image_classifier = pipeline("image-classification", model="google/vit-base-patch16-224")
ocr_reader = easyocr.Reader(['en']) 




def analyze_sentiment(text: str):
    """
    Analyzes sentiment using the loaded model and robustly maps the output label.
    """
    try:
        result = sentiment_analyzer(text)[0]
        label = result['label']


        if label.startswith('LABEL_'):
            label_id = int(label.split('_')[-1])
            config_labels = sentiment_analyzer.model.config.id2label
            readable_label = config_labels[label_id].capitalize()
        else:
            readable_label = label.capitalize()

        return {"label": readable_label, "score": result['score']}
    except Exception as e:
        print(f"Error during sentiment analysis: {e}")
        return {"label": "Neutral", "score": 0.0}

def summarize_text(text: str):
    if len(text.split()) > 50:
        result = summarizer(text, max_length=50, min_length=25, do_sample=False)
        return result[0]['summary_text']
    return "Text is too short to summarize."

def classify_topic(text: str, topics=["news", "review", "comment", "complaint"]):
    result = topic_classifier(text, candidate_labels=topics)
    return result['labels'][0] 



def classify_image(image_bytes: bytes):
    from io import BytesIO
    image = Image.open(BytesIO(image_bytes))
    result = image_classifier(image)
    return result[0]['label']

def extract_text_from_image(image_bytes: bytes):
    result = ocr_reader.readtext(image_bytes)
    extracted_text = " ".join([item[1] for item in result])
    return extracted_text

def check_toxicity(text: str):
    if not text.strip():
        return {"is_toxic": False, "score": 0.0}
    
    score = predict_prob([text])[0]
    is_toxic = score > 0.6 
    return {"is_toxic": is_toxic, "score": score}


def generate_automated_response(nlp_results: dict, cv_results: dict):
    sentiment = nlp_results.get('sentiment', {}).get('label', 'Neutral')
    is_toxic_text = nlp_results.get('toxicity', {}).get('is_toxic', False)
    
    is_toxic_ocr = cv_results.get('ocr_toxicity', {}).get('is_toxic', False)
    image_cat = cv_results.get('classification', '')

    if is_toxic_text or is_toxic_ocr:
        return "Warning: Potentially toxic content detected. Your submission will be reviewed by a moderator."

    if sentiment == 'Negative':
        return "We are sorry to hear you had a negative experience. A team member will review your feedback shortly."
        
    if sentiment == 'Positive':
        if 'product' in image_cat.lower():
            return "Thank you for the positive feedback! We're glad you're enjoying the product."
        else:
            return "Thank you for your positive feedback! We appreciate you sharing with us."

    return "Thank you for your feedback. We have received your submission."