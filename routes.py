import json
import logging
from flask import render_template, request, redirect, url_for, jsonify, flash, session
from app import app, db
from models import ScrapingSession, ScrapedData
from scraper import scrape_url, extract_elements, get_page_title, get_selector_options
from utils import export_to_csv, export_to_json, sanitize_input

# Routes
@app.route('/')
def index():
    """Render the main dashboard page"""
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    """Handle the scraping request"""
    url = sanitize_input(request.form.get('url', ''))
    selector_type = sanitize_input(request.form.get('selector_type', 'tag'))
    selector_value = sanitize_input(request.form.get('selector_value', ''))
    session_name = sanitize_input(request.form.get('session_name', ''))
    
    if not url:
        flash('Please enter a valid URL', 'danger')
        return redirect(url_for('index'))
    
    try:
        # Create a new scraping session
        new_session = ScrapingSession(
            url=url,
            selector_type=selector_type,
            selector_value=selector_value,
            name=session_name if session_name else get_page_title(url),
            status="in-progress"
        )
        db.session.add(new_session)
        db.session.commit()
        
        # Perform the scraping
        soup = scrape_url(url)
        if not soup:
            new_session.status = "failed"
            new_session.error_message = "Failed to retrieve content from URL"
            db.session.commit()
            flash('Failed to retrieve content from URL', 'danger')
            return redirect(url_for('index'))
        
        # Extract elements based on selector
        elements = extract_elements(soup, selector_type, selector_value)
        
        # Store scraped data
        for i, element in enumerate(elements):
            try:
                # Handle dictionary data (for special types like robots, meta)
                if isinstance(element, dict):
                    element_type = element.get('type', 'dict')
                    content = str(element.get('content', json.dumps(element)))
                    attributes = json.dumps(element) if element else None
                else:
                    # Regular BeautifulSoup element
                    element_type = getattr(element, 'name', 'unknown')
                    content = element.get_text(strip=True) if hasattr(element, 'get_text') else str(element)
                    attributes = json.dumps({k: v for k, v in element.attrs.items()}) if hasattr(element, 'attrs') and element.attrs else None
                
                scraped_data = ScrapedData(
                    session_id=new_session.id,
                    content=content,
                    element_type=element_type,
                    attributes=attributes,
                    index=i
                )
                db.session.add(scraped_data)
            except Exception as e:
                logging.error(f"Error processing element {i}: {str(e)}")
        
        # Update session with count and status
        new_session.item_count = len(elements)
        new_session.status = "completed"
        db.session.commit()
        
        flash(f'Successfully scraped {len(elements)} items', 'success')
        # Store the session ID in the session for immediate visualization
        session['current_session_id'] = new_session.id
        return redirect(url_for('visualization', session_id=new_session.id))
    
    except Exception as e:
        logging.error(f"Scraping error: {str(e)}")
        if new_session.id:
            new_session.status = "failed"
            new_session.error_message = str(e)
            db.session.commit()
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/history')
def history():
    """View scraping history"""
    sessions = ScrapingSession.query.order_by(ScrapingSession.timestamp.desc()).all()
    return render_template('history.html', sessions=sessions)

@app.route('/visualization/<int:session_id>')
def visualization(session_id):
    """Display visualization of scraped data"""
    session_data = ScrapingSession.query.get_or_404(session_id)
    scraped_items = ScrapedData.query.filter_by(session_id=session_id).order_by(ScrapedData.index).all()
    return render_template('visualization.html', session=session_data, items=scraped_items)

@app.route('/api/data/<int:session_id>')
def get_data(session_id):
    """API to get scraped data in JSON format"""
    session_data = ScrapingSession.query.get_or_404(session_id)
    scraped_items = ScrapedData.query.filter_by(session_id=session_id).order_by(ScrapedData.index).all()
    
    return jsonify({
        'session': session_data.to_dict(),
        'items': [item.to_dict() for item in scraped_items]
    })

@app.route('/export/<format>/<int:session_id>')
def export_data(format, session_id):
    """Export data in CSV or JSON format"""
    session_data = ScrapingSession.query.get_or_404(session_id)
    scraped_items = ScrapedData.query.filter_by(session_id=session_id).order_by(ScrapedData.index).all()
    
    if format.lower() == 'csv':
        return export_to_csv(session_data, scraped_items)
    elif format.lower() == 'json':
        return export_to_json(session_data, scraped_items)
    else:
        flash('Invalid export format', 'danger')
        return redirect(url_for('visualization', session_id=session_id))

@app.route('/help')
def help_page():
    """Display help information"""
    return render_template('help.html')

@app.route('/search', methods=['POST'])
def search():
    """Search through scraped data"""
    search_term = sanitize_input(request.form.get('search_term', ''))
    session_id = request.form.get('session_id')
    
    if not search_term:
        flash('Please enter a search term', 'warning')
        if session_id:
            return redirect(url_for('visualization', session_id=session_id))
        return redirect(url_for('history'))
    
    # If we have a session ID, search within that session
    if session_id:
        items = ScrapedData.query.filter(
            ScrapedData.session_id == session_id,
            ScrapedData.content.ilike(f'%{search_term}%')
        ).order_by(ScrapedData.index).all()
        
        session_data = ScrapingSession.query.get_or_404(session_id)
        return render_template(
            'visualization.html', 
            session=session_data, 
            items=items, 
            search_term=search_term,
            search_count=len(items)
        )
    
    # Otherwise search across all sessions
    sessions = ScrapingSession.query.join(ScrapedData).filter(
        ScrapedData.content.ilike(f'%{search_term}%')
    ).distinct().all()
    
    return render_template('history.html', sessions=sessions, search_term=search_term)

@app.route('/delete/<int:session_id>', methods=['POST'])
def delete_session(session_id):
    """Delete a scraping session and its data"""
    session_data = ScrapingSession.query.get_or_404(session_id)
    
    # Delete all associated scraped data
    ScrapedData.query.filter_by(session_id=session_id).delete()
    
    # Delete the session itself
    db.session.delete(session_data)
    db.session.commit()
    
    flash('Session deleted successfully', 'success')
    return redirect(url_for('history'))

@app.route('/api/selector-options', methods=['POST'])
def get_selectors():
    """Get recommended selector options for a given URL"""
    url = sanitize_input(request.form.get('url', ''))
    
    if not url:
        return jsonify({
            'success': False,
            'message': 'Please provide a valid URL',
            'options': None
        }), 400
    
    # Get the selector options
    selector_options = get_selector_options(url)
    
    if not selector_options:
        return jsonify({
            'success': False,
            'message': 'Failed to analyze the webpage. Please check the URL and try again.',
            'options': None
        }), 400
    
    return jsonify({
        'success': True,
        'message': 'Successfully identified selector options',
        'options': selector_options
    })
