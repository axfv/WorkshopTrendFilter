from flask import Flask, render_template_string, request
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# Initialize page number and current URL
pagenum = "1"
daynum = "1"  # Default value
current_url = f"https://steamcommunity.com/workshop/browse/?appid=550&browsesort=trend&p={pagenum}&days={daynum}"

def sanitize_string(text):
    # Extended regex pattern to match unwanted characters including various symbols
    # \u2700-\u27BF'  # Arrows
    # r'\u1F300-\u1F5FF'  # Miscellaneous Symbols and Pictographs
    # r'\u1F800-\u1F8FF'  # Supplemental Arrows-C
    # r'\u1FA70-\u1FAFF'  # Symbols for Legacy Computing
    # r'\u2600-\u26FF'    # Miscellaneous Symbols
    # r'\u27A0-\u27BF'    # Mathematical Symbols
    # r'\uFFFD'            # Replacement character
    # r'\u2000-\u200F'     # Various space and control characters   
    # r'\u2028-\u2029'     # Line and Paragraph separators    
    pattern = (r'[\u1F600-\u1F64F'  # Emoticons
    r'\u1F680-\u1F6FF'  # Transport and Map Symbols
    r'\u1F700-\u1F77F'  # Alchemical Symbols
    r'\u1F780-\u1F7FF'  # Geometric Shapes Extended
    r'\u1F900-\u1F9FF'  # Supplemental Symbols and Pictographs
    r'\u1FA00-\u1FA6F'  # Chess Symbols
    r'\u1D100-\u1D1FF'  # Musical Notation
    r'\u24EA-\u24FF'    # Enclosed Alphanumeric Supplement
    r'\u2B50'            # Star
    r'\u25B6-\u25C0'     # Play/Pause symbols
    r'\u205F'            # Medium Mathematical Space
    r'\u3000]')           # Ideographic Space

    # Remove unwanted characters
    sanitized_text = re.sub(pattern, '', text)

    return sanitized_text

def fetch_and_filter_items(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Hide unnecessary tags
    for tag in soup.find_all("div", class_="workshopBrowsePaging"):
        tag['style'] = 'display: none;'
    for tag in soup.find_all("div", id="footer"):
        tag['style'] = 'display: none;'
    
    # Hide the div containing Home link
    home_tab = soup.find("div", class_="workshop_browse_tab")
    if home_tab:
        home_tab['style'] = 'display: none;'
        
    # Hide date selection
    date_tab = soup.find("div", class_="workshopBrowseSortingControls")
    if date_tab:
        date_tab['style'] = 'display: none;'

    # Load blocklist
    blocklist = {}
    with open('blocklist.txt', 'r', encoding='utf-8') as f:
        section = None
        for line in f:
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                section = line[1:-1]
                blocklist[section] = []
            elif section:
                blocklist[section].append(line)

    # Iterate through all workshopItem elements
    items = soup.find_all("div", class_="workshopItem")

    for item in items:
        # Check [url], [nickname], and [keyword] rules
        link = item.find("a", class_="ugc")["href"]
        if any(block in link for block in blocklist.get('url', [])):
            print(f"Removing item due to blocklist rule for URL: {link}")
            item.decompose()
            next_script = item.find_next_sibling("script")
            if next_script:
                next_script.decompose()
            items = soup.find_all("div", class_="workshopItem")
            continue
        
        
        
        profile = item.find("a", class_="workshop_author_link")["href"]
        if any(block in profile for block in blocklist.get('nickname', [])):
            print(f"Removing item due to blocklist rule for nickname: {link}")
            item.decompose()
            next_script = item.find_next_sibling("script")
            if next_script:
                next_script.decompose()
            items = soup.find_all("div", class_="workshopItem")
            continue        
        '''
        if any(nickname in item_text for nickname in blocklist.get('nickname', [])):
            print(f"Removing item due to blocklist rule for nickname: {item_text}")
            item.decompose()
            next_script = item.find_next_sibling("script")
            if next_script:
                next_script.decompose()
            items = soup.find_all("div", class_="workshopItem")
            continue
        '''
        
        item_text = item.get_text(strip=True)
        
        # Check [charset] rules
        if 'sc' in blocklist.get('charset', []):
            item_contains_chinese = re.search(r'[\u4e00-\u9fff]', item_text)
            next_script = item.find_next_sibling("script")
            should_remove_item = False
            
            if next_script and next_script.string:
                title_match = re.search(r'"title":"(.*?)"', next_script.string)
                description_match = re.search(r'"description":"(.*?)"', next_script.string)
                # Decode and sanitize title and description
                title = (sanitize_string(title_match.group(1).encode().decode('unicode-escape')) if title_match else None)
                description = (sanitize_string(description_match.group(1).encode().decode('unicode-escape')) if description_match else None)

                if title and re.search(r'[\u4e00-\u9fff]', title):
                    print(f"Removing item due to Simplified Chinese characters in title: {title}")
                    should_remove_item = True

                if description and re.search(r'[\u4e00-\u9fff]', description):
                    print(f"Removing item due to Simplified Chinese characters in description: {description}")
                    should_remove_item = True
            
            if item_contains_chinese or should_remove_item:
                print(f"Removing item due to Simplified Chinese characters in content.")
                item.decompose()
                if next_script:
                    next_script.decompose()
                items = soup.find_all("div", class_="workshopItem")
                continue
        
        # Check keywords in script's title and description
        keywords = blocklist.get('keyword', [])
        should_remove_item = False
        next_script = item.find_next_sibling("script")
        
        if next_script and next_script.string:
            title_match = re.search(r'"title":"(.*?)"', next_script.string)
            description_match = re.search(r'"description":"(.*?)"', next_script.string)
            # Decode and sanitize title and description
            title = (sanitize_string(title_match.group(1).encode().decode('unicode-escape')) if title_match else None)
            description = (sanitize_string(description_match.group(1).encode().decode('unicode-escape')) if description_match else None)
            
            if any(keyword in title for keyword in keywords):
                print(f"Removing item due to keyword in title: {title}")
                should_remove_item = True
            
            if any(keyword in description for keyword in keywords):
                print(f"Removing item due to keyword in description: {description}")
                should_remove_item = True

        # If removal is needed, perform the operation
        if should_remove_item:
            item.decompose()
            if next_script:
                next_script.decompose()
            items = soup.find_all("div", class_="workshopItem")

    # Return the processed HTML
    return str(soup)

def fetch_current_page_links(soup):
    links = []
    for link in soup.find_all('a', class_='pagelink'):
        page_number = link.text.replace(',', '')
        links.append(page_number)
    return links # Return only page number texts
    '''
    pagination_controls = soup.find("div", class_="workshopBrowsePagingControls")
    pages = pagination_controls.find_all("a", class_="pagelink")
    return [page.text for page in pages]  # Return only page number texts
    '''    

@app.route('/')
def index():
    global current_url
    processed_html = fetch_and_filter_items(current_url)
    soup = BeautifulSoup(processed_html, 'html.parser')

    pagination_links = fetch_current_page_links(soup)
    pagination_html = [f'<a class="pagelink" href="/fetch?p={link}&days={daynum}">{link}</a>' for link in pagination_links]

    # Add days hyperlinks
    days_options = [1, 7, 30, 90, 180, 365, -1]
    days_links = ''.join([f'<a href="/fetch?p=1&days={day}" style="margin-right: 10px; color: white;">{day} Days</a>' for day in days_options])

    return render_template_string(f"""
        <style>
            body {{
                margin: 0;
                padding-top: 100px; /* Leave space for content below */
            }}
            .fixed-header {{
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                background-color: black; /* Black background */
                color: white; /* White text */
                padding: 10px;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.5);
                z-index: 1000;
            }}
            #items {{
                margin-top: 20px; /* Space below content */
            }}
            a {{
                color: white; /* Hyperlink text in white */
                text-decoration: none; /* Remove underline */
            }}
            a:hover {{
                text-decoration: underline; /* Show underline on hover */
            }}
        </style>
        <div class="fixed-header">
            <!--<h1>Steam Workshop</h1>-->
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <label>Select Days:</label> {days_links}
                </div>
                <div style="display: flex;">
                    <label style="margin-right: 5px;">Pages:</label>
                    <div id="pagination" style="margin-left: 10px;">
                        {' / '.join(pagination_html)}
                    </div>
                </div>
            </div>
        </div>
        <div id="items">{soup}</div>
    """)

@app.route('/fetch', methods=['GET'])
def fetch():
    global current_url, pagenum, daynum
    page_num = request.args.get('p')  # Get the clicked page number
    days_param = request.args.get('days')  # Get the selected days

    if days_param:  # Update daynum if days parameter is provided
        daynum = days_param
    if page_num:  # Update pagenum if page number parameter is provided
        pagenum = max(1, min(1000, int(page_num)))  # Compact page number limit
    
    # Update current_url
    current_url = f"https://steamcommunity.com/workshop/browse/?appid=550&browsesort=trend&p={pagenum}&days={daynum}"

    # Crawl and process
    processed_html = fetch_and_filter_items(current_url)
    soup = BeautifulSoup(processed_html, 'html.parser')

    pagination_links = fetch_current_page_links(soup)
    pagination_html = [f'<a class="pagelink" href="/fetch?p={link}&days={daynum}">{link}</a>' for link in pagination_links]

    # Add days hyperlinks
    days_options = [1, 7, 30, 90, 180, 365, -1]
    days_links = ''.join([f'<a href="/fetch?p=1&days={day}" style="margin-right: 10px; color: white;">{day} Days</a>' for day in days_options])

    return render_template_string(f"""
        <style>
            body {{
                margin: 0;
                padding-top: 100px;
            }}
            .fixed-header {{
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                background-color: black;
                color: white;
                padding: 10px;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.5);
                z-index: 1000;
            }}
            #items {{
                margin-top: 20px;
            }}
            a {{
                color: white;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
        </style>
        <script>
            document.addEventListener('keydown', function(event) {{
                if (event.key === 'ArrowLeft') {{
                    window.location.href = '/fetch?p={int(pagenum) - 1}&days={daynum}';
                }} else if (event.key === 'ArrowRight') {{
                    window.location.href = '/fetch?p={int(pagenum) + 1}&days={daynum}';
                }}
            }});
        </script>
        <div class="fixed-header">
            <!--<h1>Steam Workshop</h1>-->
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <label>Select Days:</label> {days_links}
                </div>
                <div style="display: flex;">
                    <label style="margin-right: 5px;">Pages:</label>
                    <div id="pagination" style="margin-left: 10px;">
                        {' / '.join(pagination_html)}
                    </div>
                </div>
            </div>
        </div>
        <div id="items">{soup}</div>
    """)

if __name__ == '__main__':
    app.run(debug=True)
