import logging
import requests
from bs4 import BeautifulSoup
import urllib.parse
from collections import Counter
import json
import re

# Note: trafilatura is imported dynamically in the extract_text_content function to handle import errors gracefully

def scrape_url(url):
    """
    Scrape a URL and return a BeautifulSoup object.
    
    Args:
        url (str): The URL to scrape
        
    Returns:
        BeautifulSoup: The parsed HTML content or None if an error occurs
    """
    try:
        # Check if URL is valid
        parsed_url = urllib.parse.urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            logging.error(f"Invalid URL: {url}")
            return None
        
        # Set user agent to avoid blocking
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make the request
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Store the original URL in the soup object for reference
        # We use __dict__ to store custom attributes since BeautifulSoup doesn't have a url attribute
        soup.__dict__['url'] = url
        
        return soup
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"General error in scrape_url: {str(e)}")
        return None

def extract_elements(soup, selector_type, selector_value):
    """
    Extract elements from a BeautifulSoup object based on the selector.
    
    Args:
        soup (BeautifulSoup): The parsed HTML
        selector_type (str): The type of selector (tag, class, id, css, images, links, robots, meta)
        selector_value (str): The value of the selector
        
    Returns:
        list: A list of matching BeautifulSoup elements or data objects
    """
    if not soup:
        return []
    
    # Default to getting all elements if no selector is provided
    if not selector_value and selector_type not in ['tag', 'images', 'links', 'robots', 'meta']:
        return []
    
    try:
        # Traditional selectors
        if selector_type == 'tag':
            if not selector_value:
                # If no tag is specified, get all tags in the body
                return soup.find_all() if not soup.body else soup.body.find_all()
            return soup.find_all(selector_value)
        elif selector_type == 'class':
            return soup.find_all(class_=selector_value)
        elif selector_type == 'id':
            # Since IDs are unique, we wrap it in a list
            element = soup.find(id=selector_value)
            return [element] if element else []
        elif selector_type == 'css':
            # Basic CSS selector support
            return soup.select(selector_value)
            
        # Special selector types
        elif selector_type == 'images':
            return extract_image_elements(soup, selector_value)
        elif selector_type == 'links':
            return extract_link_elements(soup, selector_value)
        elif selector_type == 'robots':
            return extract_robots_data(soup.__dict__.get('url') if 'url' in soup.__dict__ else None)
        elif selector_type == 'meta':
            return extract_meta_elements(soup, selector_value)
        else:
            logging.warning(f"Unsupported selector type: {selector_type}")
            return []
    except Exception as e:
        logging.error(f"Error extracting elements: {str(e)}")
        return []
        
def extract_image_elements(soup, image_type='All Images'):
    """
    Extract image elements from the page.
    
    Args:
        soup (BeautifulSoup): The parsed HTML
        image_type (str): The type of images to extract (All Images, Large Images Only, etc)
        
    Returns:
        list: A list of image elements
    """
    if not soup:
        return []
        
    # Get all image elements
    all_images = soup.find_all('img')
    
    # Filter based on image type
    if image_type == 'All Images':
        return all_images
    elif image_type == 'Large Images Only':
        # Filter for images that might be large (width or height attributes)
        large_images = []
        for img in all_images:
            # Check for width/height attributes or size in style
            width = img.get('width')
            height = img.get('height')
            style = img.get('style', '')
            
            # Convert to integers if possible
            try:
                width = int(width) if width and width.isdigit() else 0
                height = int(height) if height and height.isdigit() else 0
            except (ValueError, TypeError):
                width, height = 0, 0
                
            # Check for size in style attribute
            width_in_style = re.search(r'width\s*:\s*(\d+)', style)
            height_in_style = re.search(r'height\s*:\s*(\d+)', style)
            
            if width_in_style:
                width = int(width_in_style.group(1))
            if height_in_style:
                height = int(height_in_style.group(1))
                
            # If width or height is over 200px, consider it large
            if width > 200 or height > 200:
                large_images.append(img)
                
        return large_images
    elif image_type == 'Product Images':
        # Look for images that might be product images
        product_images = []
        product_indicators = ['product', 'item', 'thumbnail', 'gallery', 'goods', 'merch']
        
        for img in all_images:
            # Check for product-related attributes
            alt_text = img.get('alt', '').lower()
            img_class = ' '.join(img.get('class', [])).lower()
            img_id = img.get('id', '').lower()
            img_src = img.get('src', '').lower()
            
            # Check if any product indicators are in attributes
            if any(indicator in attr for indicator in product_indicators for attr in [alt_text, img_class, img_id, img_src]):
                product_images.append(img)
                
        return product_images
    elif image_type == 'Banner Images':
        # Look for images that might be banners
        banner_images = []
        banner_indicators = ['banner', 'hero', 'slide', 'carousel', 'header', 'cover', 'featured']
        
        for img in all_images:
            # Check for banner-related attributes
            alt_text = img.get('alt', '').lower()
            img_class = ' '.join(img.get('class', [])).lower()
            img_id = img.get('id', '').lower()
            
            # Check if any banner indicators are in attributes
            if any(indicator in attr for indicator in banner_indicators for attr in [alt_text, img_class, img_id]):
                banner_images.append(img)
                
        return banner_images
    else:
        return all_images

def extract_link_elements(soup, link_type='All Links'):
    """
    Extract link elements from the page.
    
    Args:
        soup (BeautifulSoup): The parsed HTML
        link_type (str): The type of links to extract
        
    Returns:
        list: A list of link elements
    """
    if not soup:
        return []
        
    # Get all link elements
    all_links = soup.find_all('a', href=True)
    
    # Get the base URL to determine internal vs external links
    base_url = None
    base_tag = soup.find('base', href=True)
    if base_tag:
        base_url = base_tag['href']
        
    # If we don't have a base URL from a <base> tag, try to extract from page URL
    if not base_url and 'url' in soup.__dict__:
        parsed_url = urllib.parse.urlparse(soup.__dict__.get('url'))
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    # Filter based on link type
    if link_type == 'All Links':
        return all_links
    elif link_type == 'Internal Links':
        # If we don't have a base URL, we can't determine internal links
        if not base_url:
            return all_links
            
        internal_links = []
        for link in all_links:
            href = link['href']
            # Skip fragment-only links
            if href.startswith('#'):
                continue
                
            # Handle relative URLs
            if not href.startswith(('http://', 'https://', '//')):
                internal_links.append(link)
            else:
                # Check if link is to the same domain
                parsed_href = urllib.parse.urlparse(href)
                href_domain = f"{parsed_href.scheme}://{parsed_href.netloc}"
                if href_domain == base_url:
                    internal_links.append(link)
                    
        return internal_links
    elif link_type == 'External Links':
        # If we don't have a base URL, we can't determine external links
        if not base_url:
            return []
            
        external_links = []
        for link in all_links:
            href = link['href']
            # Skip fragment-only or relative links
            if href.startswith('#') or not href.startswith(('http://', 'https://', '//')):
                continue
                
            # Check if link is to a different domain
            parsed_href = urllib.parse.urlparse(href)
            href_domain = f"{parsed_href.scheme}://{parsed_href.netloc}"
            if href_domain != base_url:
                external_links.append(link)
                    
        return external_links
    elif link_type == 'Navigation Links':
        # Look for links that are likely part of navigation
        nav_links = []
        nav_containers = soup.select('nav, .nav, .navigation, .menu, header, .header, .navbar')
        
        for container in nav_containers:
            nav_links.extend(container.find_all('a', href=True))
            
        return nav_links
    elif link_type == 'Footer Links':
        # Look for links in the footer
        footer_links = []
        footer_containers = soup.select('footer, .footer, #footer')
        
        for container in footer_containers:
            footer_links.extend(container.find_all('a', href=True))
            
        return footer_links
    else:
        return all_links

def extract_robots_data(url):
    """
    Analyze the robots.txt file of a website.
    
    Args:
        url (str): The URL of the website
        
    Returns:
        list: A list containing a single dictionary with robots.txt data
    """
    if not url:
        return [{'content': 'No URL provided for robots.txt analysis'}]
        
    try:
        # Extract the domain from the URL
        parsed_url = urllib.parse.urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        robots_url = f"{base_url}/robots.txt"
        
        # Fetch the robots.txt file
        response = requests.get(robots_url, timeout=5)
        
        # Check if we got a successful response
        if response.status_code == 200:
            content = response.text
            
            # Parse the robots.txt content
            user_agents = []
            disallowed = []
            allowed = []
            sitemaps = []
            
            current_agent = "*"  # Default user agent
            
            for line in content.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                # Check for user-agent
                if line.lower().startswith('user-agent:'):
                    agent = line[11:].strip()
                    current_agent = agent
                    if agent not in user_agents:
                        user_agents.append(agent)
                        
                # Check for disallow
                elif line.lower().startswith('disallow:'):
                    path = line[9:].strip()
                    if path:
                        disallowed.append(f"{current_agent}: {path}")
                        
                # Check for allow
                elif line.lower().startswith('allow:'):
                    path = line[6:].strip()
                    if path:
                        allowed.append(f"{current_agent}: {path}")
                        
                # Check for sitemap
                elif line.lower().startswith('sitemap:'):
                    sitemap = line[8:].strip()
                    if sitemap:
                        sitemaps.append(sitemap)
            
            # Create a formatted content string for display
            content_summary = (
                f"Robots.txt Analysis for {base_url}\n\n"
                f"User-Agents: {', '.join(user_agents[:5]) if user_agents else 'None'}\n\n"
                f"Disallowed Paths ({len(disallowed)}):\n" + 
                '\n'.join([f"- {path}" for path in disallowed[:10]]) + 
                (f"\n... and {len(disallowed)-10} more" if len(disallowed) > 10 else "") + 
                f"\n\nAllowed Paths ({len(allowed)}):\n" + 
                '\n'.join([f"- {path}" for path in allowed[:10]]) + 
                (f"\n... and {len(allowed)-10} more" if len(allowed) > 10 else "") + 
                f"\n\nSitemaps ({len(sitemaps)}):\n" + 
                '\n'.join([f"- {url}" for url in sitemaps[:5]]) +
                (f"\n... and {len(sitemaps)-5} more" if len(sitemaps) > 5 else "")
            )
            
            # Create the result object with type field for compatibility
            result = {
                'type': 'robots_data',
                'status': 'Success',
                'robots_url': robots_url,
                'user_agents': user_agents,
                'disallowed_paths': disallowed[:10],  # Limit to first 10
                'allowed_paths': allowed[:10],        # Limit to first 10
                'sitemaps': sitemaps,
                'content': content_summary
            }
            
            return [result]
        else:
            error_result = {
                'type': 'robots_error',
                'status': 'Error', 
                'message': f"Could not fetch robots.txt: HTTP {response.status_code}",
                'content': f"Error: Could not fetch robots.txt file from {robots_url} (HTTP {response.status_code})"
            }
            return [error_result]
    except Exception as e:
        logging.error(f"Error fetching robots.txt: {str(e)}")
        error_result = {
            'type': 'robots_error',
            'status': 'Error', 
            'message': f"Error fetching robots.txt: {str(e)}",
            'content': f"Error: Could not fetch or process robots.txt file from {url}. Exception: {str(e)}"
        }
        return [error_result]

def extract_meta_elements(soup, meta_type='All Meta Tags'):
    """
    Extract meta information from the page.
    
    Args:
        soup (BeautifulSoup): The parsed HTML
        meta_type (str): The type of meta information to extract
        
    Returns:
        list: A list of meta elements or data objects
    """
    if not soup:
        return []
        
    results = []
    
    # Function to wrap metadata in an element-like object
    def create_meta_object(content, name=None, property=None):
        return {
            'name': name,
            'property': property,
            'content': content
        }
    
    # Extract title
    title = soup.find('title')
    title_text = title.string.strip() if title else "No title found"
    
    # Extract description
    desc_meta = soup.find('meta', attrs={'name': 'description'})
    description = desc_meta['content'] if desc_meta and desc_meta.has_attr('content') else "No description found"
    
    # Extract keywords
    keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
    keywords = keywords_meta['content'] if keywords_meta and keywords_meta.has_attr('content') else "No keywords found"
    
    # Extract Open Graph data
    og_title = soup.find('meta', attrs={'property': 'og:title'})
    og_title = og_title['content'] if og_title and og_title.has_attr('content') else "No OG title found"
    
    og_desc = soup.find('meta', attrs={'property': 'og:description'})
    og_desc = og_desc['content'] if og_desc and og_desc.has_attr('content') else "No OG description found"
    
    og_image = soup.find('meta', attrs={'property': 'og:image'})
    og_image = og_image['content'] if og_image and og_image.has_attr('content') else "No OG image found"
    
    # Extract Twitter Card data
    twitter_card = soup.find('meta', attrs={'name': 'twitter:card'})
    twitter_card = twitter_card['content'] if twitter_card and twitter_card.has_attr('content') else "No Twitter card found"
    
    twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
    twitter_title = twitter_title['content'] if twitter_title and twitter_title.has_attr('content') else "No Twitter title found"
    
    # Process based on meta type
    if meta_type == 'All Meta Tags':
        # Get all meta tags
        results.append(create_meta_object(title_text, name='title'))
        results.append(create_meta_object(description, name='description'))
        results.append(create_meta_object(keywords, name='keywords'))
        
        # Add all other meta tags
        for meta in soup.find_all('meta'):
            if meta.has_attr('name') and meta.has_attr('content'):
                results.append(create_meta_object(meta['content'], name=meta['name']))
            elif meta.has_attr('property') and meta.has_attr('content'):
                results.append(create_meta_object(meta['content'], property=meta['property']))
                
    elif meta_type == 'Title & Description':
        results.append(create_meta_object(title_text, name='title'))
        results.append(create_meta_object(description, name='description'))
        
    elif meta_type == 'Keywords':
        results.append(create_meta_object(keywords, name='keywords'))
        
    elif meta_type == 'Open Graph Data':
        results.append(create_meta_object(og_title, property='og:title'))
        results.append(create_meta_object(og_desc, property='og:description'))
        results.append(create_meta_object(og_image, property='og:image'))
        
        # Add other og: tags
        for meta in soup.find_all('meta'):
            if meta.has_attr('property') and meta.has_attr('content'):
                prop = meta['property']
                if prop.startswith('og:') and prop not in ['og:title', 'og:description', 'og:image']:
                    results.append(create_meta_object(meta['content'], property=prop))
                    
    elif meta_type == 'Twitter Cards':
        results.append(create_meta_object(twitter_card, name='twitter:card'))
        results.append(create_meta_object(twitter_title, name='twitter:title'))
        
        # Add other twitter: tags
        for meta in soup.find_all('meta'):
            if meta.has_attr('name') and meta.has_attr('content'):
                name = meta['name']
                if name.startswith('twitter:') and name not in ['twitter:card', 'twitter:title']:
                    results.append(create_meta_object(meta['content'], name=name))
    
    return results

def get_page_title(url):
    """
    Get the title of a web page.
    
    Args:
        url (str): The URL of the web page
        
    Returns:
        str: The title of the web page or a default title
    """
    try:
        soup = scrape_url(url)
        if soup and soup.title and soup.title.string:
            return soup.title.string.strip()
        return "Scraping Session"
    except Exception as e:
        logging.error(f"Error getting page title: {str(e)}")
        return "Scraping Session"

def extract_text_content(url):
    """
    Extract clean text content from a URL using trafilatura.
    
    Args:
        url (str): The URL to extract content from
        
    Returns:
        str: The extracted text content or None if failed
    """
    try:
        # Import trafilatura here to handle potential import errors gracefully
        import trafilatura
        
        # Fetch and extract the content
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded)
        return text
    except ImportError:
        logging.error("trafilatura library not found. Install with 'pip install trafilatura'")
        return f"Error: The trafilatura library is required for text extraction. Content not available."
    except Exception as e:
        logging.error(f"Error extracting text content: {str(e)}")
        return None
        
def identify_important_elements(soup):
    """
    Identify important elements in a webpage for scraping.
    
    Args:
        soup (BeautifulSoup): The parsed HTML
        
    Returns:
        dict: A dictionary containing lists of important selectors by type
    """
    if not soup:
        return {
            'tags': [],
            'classes': [],
            'ids': [],
            'css': [],
            'images': [],
            'links': []
        }
    
    # Initialize result dictionary
    results = {
        'tags': [],
        'classes': [],
        'ids': [],
        'css': [],
        'images': [],
        'links': []
    }
    
    # Identify important tags (elements with substantial content)
    content_tags = ['div', 'article', 'section', 'p', 'h1', 'h2', 'h3', 'main', 'header', 'footer', 'nav', 'aside', 'ul', 'ol', 'table', 'a']
    
    # Add all important tags by default
    results['tags'] = content_tags
    
    # Find important classes (those used multiple times and associated with content)
    all_classes = []
    for tag in soup.find_all(True):
        if 'class' in tag.attrs:
            # Flatten the list if it's a list
            if isinstance(tag['class'], list):
                all_classes.extend(tag['class'])
            else:
                all_classes.append(tag['class'])
    
    # Count occurrences of each class
    class_counter = Counter(all_classes)
    
    # Choose classes that appear multiple times (likely pattern indicators)
    # and those with semantically meaningful names
    semantic_patterns = [
        'content', 'article', 'post', 'entry', 'main', 'container', 
        'wrapper', 'body', 'text', 'item', 'card', 'list', 'grid', 
        'product', 'news', 'story', 'blog', 'title', 'headline',
        'header', 'footer', 'author', 'date', 'time', 'price'
    ]
    
    important_classes = []
    
    # Add classes that appear multiple times
    for cls, count in class_counter.items():
        if count > 2:
            important_classes.append(cls)
    
    # Add classes with semantically meaningful names
    for cls in all_classes:
        if cls and any(pattern in cls.lower() for pattern in semantic_patterns):
            if cls not in important_classes:
                important_classes.append(cls)
    
    # Limit to 15 most common classes to avoid overwhelming
    results['classes'] = important_classes[:15]
    
    # Find important IDs (those associated with main content)
    important_ids = []
    for tag in soup.find_all(id=True):
        id_val = tag['id']
        # Check if ID seems meaningful for content
        if any(pattern in id_val.lower() for pattern in ['content', 'main', 'article', 'post', 'container', 'wrapper']):
            important_ids.append(id_val)
    
    results['ids'] = important_ids
    
    # Generate some useful CSS selectors
    # Main content areas
    article_selectors = ['article', 'main', 'div.content', 'div.main', 'div.article', 'div#content', 'div#main', 'section.content']
    # List items
    list_selectors = ['ul li', 'ol li', 'div.item', '.items > *', '.list > *', '.articles > *', '.products > *']
    # Headings
    heading_selectors = ['h1', 'h2', 'h3', '.title', '.heading', '.headline']
    
    # Check which selectors actually match elements on the page
    results['css'] = []
    for selector in article_selectors + list_selectors + heading_selectors:
        try:
            if soup.select(selector):
                results['css'].append(selector)
        except:
            pass
    
    # Find image categories available on the page
    all_images = soup.find_all('img')
    if all_images:
        # Always include "All Images" as an option
        results['images'] = ['All Images']
        
        # Check for large images
        large_images = []
        for img in all_images:
            width = img.get('width')
            height = img.get('height')
            style = img.get('style', '')
            
            try:
                width = int(width) if width and width.isdigit() else 0
                height = int(height) if height and height.isdigit() else 0
            except (ValueError, TypeError):
                width, height = 0, 0
                
            # Check for size in style attribute
            width_in_style = re.search(r'width\s*:\s*(\d+)', style)
            height_in_style = re.search(r'height\s*:\s*(\d+)', style)
            
            if width_in_style:
                width = int(width_in_style.group(1))
            if height_in_style:
                height = int(height_in_style.group(1))
                
            if width > 200 or height > 200:
                large_images.append(img)
        
        if large_images:
            results['images'].append('Large Images Only')
            
        # Check for product images
        product_indicators = ['product', 'item', 'thumbnail', 'gallery', 'goods', 'merch']
        product_images = []
        
        for img in all_images:
            alt_text = img.get('alt', '').lower()
            img_class = ' '.join(img.get('class', [])).lower() if img.get('class') else ''
            img_id = img.get('id', '').lower()
            img_src = img.get('src', '').lower()
            
            if any(indicator in attr for indicator in product_indicators for attr in [alt_text, img_class, img_id, img_src]):
                product_images.append(img)
                
        if product_images:
            results['images'].append('Product Images')
            
        # Check for banner images
        banner_indicators = ['banner', 'hero', 'slide', 'carousel', 'header', 'cover', 'featured']
        banner_images = []
        
        for img in all_images:
            alt_text = img.get('alt', '').lower()
            img_class = ' '.join(img.get('class', [])).lower() if img.get('class') else ''
            img_id = img.get('id', '').lower()
            
            if any(indicator in attr for indicator in banner_indicators for attr in [alt_text, img_class, img_id]):
                banner_images.append(img)
                
        if banner_images:
            results['images'].append('Banner Images')
    
    # Find link categories available on the page
    all_links = soup.find_all('a', href=True)
    if all_links:
        # Always include "All Links" as an option
        results['links'] = ['All Links']
        
        # Get the base URL to determine internal vs external links
        base_url = None
        base_tag = soup.find('base', href=True)
        if base_tag:
            base_url = base_tag['href']
            
        # If we don't have a base URL from a <base> tag, try to extract from page URL
        if not base_url and 'url' in soup.__dict__:
            parsed_url = urllib.parse.urlparse(soup.__dict__.get('url'))
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        if base_url:
            # Check for internal and external links
            internal_links = []
            external_links = []
            
            for link in all_links:
                href = link['href']
                # Skip fragment-only links
                if href.startswith('#'):
                    continue
                    
                # Handle relative URLs
                if not href.startswith(('http://', 'https://', '//')):
                    internal_links.append(link)
                else:
                    # Check if link is to the same domain
                    parsed_href = urllib.parse.urlparse(href)
                    href_domain = f"{parsed_href.scheme}://{parsed_href.netloc}"
                    if href_domain == base_url:
                        internal_links.append(link)
                    else:
                        external_links.append(link)
                        
            if internal_links:
                results['links'].append('Internal Links')
            if external_links:
                results['links'].append('External Links')
        
        # Check for navigation links
        nav_containers = soup.select('nav, .nav, .navigation, .menu, header, .header, .navbar')
        nav_links = []
        
        for container in nav_containers:
            nav_links.extend(container.find_all('a', href=True))
            
        if nav_links:
            results['links'].append('Navigation Links')
            
        # Check for footer links
        footer_containers = soup.select('footer, .footer, #footer')
        footer_links = []
        
        for container in footer_containers:
            footer_links.extend(container.find_all('a', href=True))
            
        if footer_links:
            results['links'].append('Footer Links')
    
    return results

def get_selector_options(url):
    """
    Get a list of recommended selector options for the given URL.
    
    Args:
        url (str): The URL to analyze
        
    Returns:
        dict: A dictionary containing lists of selectors by type
    """
    try:
        soup = scrape_url(url)
        if not soup:
            return None
        
        return identify_important_elements(soup)
    except Exception as e:
        logging.error(f"Error identifying selectors: {str(e)}")
        return None
