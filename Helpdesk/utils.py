import speech_recognition as sr
from textblob import TextBlob
import os
import io

def analyze_audio(filepath):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(filepath) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            
            # Sentiment Analysis
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            
            if polarity > 0.1:
                sentiment = 'Positive'
            elif polarity < -0.1:
                sentiment = 'Negative'
            else:
                sentiment = 'Neutral'
                
            confidence = abs(polarity) * 100
            if confidence == 0 and sentiment == 'Neutral':
                # Just base it on subjectivity or an arbitrary high if exactly neutral
                confidence = 85.0
                
            # Bonus: Summary and Keywords
            # using TextBlob noun phrases for keywords
            keywords = ", ".join(blob.noun_phrases[:5])
            
            # Simple summary (first sentence)
            summary = text.split('.')[0] + "." if '.' in text else text
            
            return {
                "success": True,
                "transcript": text,
                "sentiment": sentiment,
                "confidence": round(confidence, 2),
                "summary": summary,
                "keywords": keywords
            }
    except Exception as e:
        return {"success": False, "error": str(e)}
