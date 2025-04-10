from datetime import datetime
from app import db

class ScrapingSession(db.Model):
    """Model for storing scraping session information"""
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(512), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    selector_type = db.Column(db.String(20), nullable=True)  # tag, class, id
    selector_value = db.Column(db.String(100), nullable=True)
    item_count = db.Column(db.Integer, default=0)
    name = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default="completed")  # completed, failed, in-progress
    error_message = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'selector_type': self.selector_type,
            'selector_value': self.selector_value,
            'item_count': self.item_count,
            'name': self.name,
            'status': self.status,
            'error_message': self.error_message
        }

class ScrapedData(db.Model):
    """Model for storing the actual scraped data"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('scraping_session.id'), nullable=False)
    content = db.Column(db.Text, nullable=True)
    content_type = db.Column(db.String(50), default="text")  # text, html, etc.
    element_type = db.Column(db.String(20), nullable=True)  # The HTML tag type
    attributes = db.Column(db.Text, nullable=True)  # JSON string of attributes
    index = db.Column(db.Integer, nullable=False)  # Order within the scraping results
    
    # Relationship
    session = db.relationship('ScrapingSession', backref=db.backref('data_items', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'content': self.content,
            'content_type': self.content_type, 
            'element_type': self.element_type,
            'attributes': self.attributes,
            'index': self.index
        }
