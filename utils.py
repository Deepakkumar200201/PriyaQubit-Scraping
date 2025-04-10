import csv
import io
import json
import re
from flask import make_response, jsonify
import logging
import html

def sanitize_input(input_str):
    """
    Sanitize user input to prevent security issues
    
    Args:
        input_str (str): The input string to sanitize
        
    Returns:
        str: The sanitized string
    """
    if not input_str:
        return ""
    
    # Convert to string if it's not already
    input_str = str(input_str)
    
    # HTML escape to prevent XSS
    sanitized = html.escape(input_str)
    
    return sanitized

def export_to_csv(session_data, scraped_items):
    """
    Export scraped data to CSV format
    
    Args:
        session_data (ScrapingSession): The scraping session
        scraped_items (list): List of ScrapedData items
        
    Returns:
        Response: A Flask response with the CSV data
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(['Index', 'Element Type', 'Content', 'Attributes'])
    
    # Write data
    for item in scraped_items:
        attributes = item.attributes if item.attributes else '{}'
        writer.writerow([
            item.index,
            item.element_type,
            item.content,
            attributes
        ])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename=scraping_session_{session_data.id}.csv"
    response.headers["Content-type"] = "text/csv"
    
    return response

def export_to_json(session_data, scraped_items):
    """
    Export scraped data to JSON format
    
    Args:
        session_data (ScrapingSession): The scraping session
        scraped_items (list): List of ScrapedData items
        
    Returns:
        Response: A Flask response with the JSON data
    """
    data = {
        'session': session_data.to_dict(),
        'items': [item.to_dict() for item in scraped_items]
    }
    
    # Create response
    response = make_response(jsonify(data))
    response.headers["Content-Disposition"] = f"attachment; filename=scraping_session_{session_data.id}.json"
    response.headers["Content-type"] = "application/json"
    
    return response

def get_data_summary(scraped_items):
    """
    Generate a summary of the scraped data
    
    Args:
        scraped_items (list): List of ScrapedData items
        
    Returns:
        dict: A summary of the data
    """
    if not scraped_items:
        return {
            'total_items': 0,
            'element_types': {},
            'avg_content_length': 0,
            'longest_content': {'index': None, 'length': 0},
            'shortest_content': {'index': None, 'length': 0}
        }
    
    element_types = {}
    total_length = 0
    longest = {'index': None, 'length': 0}
    shortest = {'index': None, 'length': float('inf')}
    
    for item in scraped_items:
        # Count element types
        element_type = item.element_type or 'unknown'
        element_types[element_type] = element_types.get(element_type, 0) + 1
        
        # Calculate content length
        content_length = len(item.content) if item.content else 0
        total_length += content_length
        
        # Track longest content
        if content_length > longest['length']:
            longest = {'index': item.index, 'length': content_length}
            
        # Track shortest content
        if content_length < shortest['length'] and content_length > 0:
            shortest = {'index': item.index, 'length': content_length}
    
    # If no shortest was found (all empty)
    if shortest['length'] == float('inf'):
        shortest = {'index': None, 'length': 0}
    
    return {
        'total_items': len(scraped_items),
        'element_types': element_types,
        'avg_content_length': total_length / len(scraped_items) if scraped_items else 0,
        'longest_content': longest,
        'shortest_content': shortest
    }
