from textblob import TextBlob

def analyze_sentiment(text):
    """
    Analyzes sentiment of a text string using TextBlob.
    Returns a score between -1 (negative) and 1 (positive).
    """
    blob = TextBlob(text)
    return blob.sentiment.polarity

def analyze_news_sentiment(news_items):
    """
    Analyzes sentiment for a list of news items.
    Returns the average sentiment score and the processed items with scores.
    """
    if not news_items:
        return 0, []
    
    processed_news = []
    total_sentiment = 0
    
    for item in news_items:
        title = item.get('title', '')
        score = analyze_sentiment(title)
        item['sentiment'] = score
        processed_news.append(item)
        total_sentiment += score
        
    avg_sentiment = total_sentiment / len(news_items)
    return avg_sentiment, processed_news
