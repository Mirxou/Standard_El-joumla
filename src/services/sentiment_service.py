from textblob import TextBlob


class SentimentService:
    """
    The 'Emotion AI': Analyzes text sentiment for Chatter and Feedback.
    Returns: Polarity (-1.0 to 1.0) and Label.
    """

    def __init__(self):
        pass

    def analyze(self, text):
        if not text:
            return 0.0, "Neutral"

        blob = TextBlob(text)
        polarity = blob.sentiment.polarity

        if polarity > 0.1:
            return polarity, "Positive"
        elif polarity < -0.1:
            return polarity, "Negative"
        else:
            return polarity, "Neutral"

    def get_emoji(self, label):
        if label == "Positive":
            return "😊"
        if label == "Negative":
            return "😡"
        return "😐"
