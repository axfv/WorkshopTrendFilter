# WorkshopTrendFilter

A Flask web application that filters Steam Workshop trend items based on a block list.

## Requirements

- Python 3.10

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/axfv/WorkshopTrendFilter.git
   cd WorkshopTrendFilter   
2. Install required packages::
   ```bash
   pip install -r requirements.txt

## Usage
* Run the Flask app using:
   ```bash
   python app.py
* Insert your rules into blocklist.txt, ensure there are no empty lines.
* Access the link you can copy from the console, usually http://127.0.0.1:5000.
The format is as follows:
\[url\]
specify addon url 1
specify addon url 2
specify addon url 3
\[nickname\]
specify author profile url 1
specify author profile url 2
specify author profile url 3
\[keyword\]
\[charset\]
### How to Get Addon URLs 
1. **Using a Web Browser (like Edge)**: Right-click on the addon image and select "Copy link" from the menu.
2. **Using the Steam Client**: Right-click on the addon image and choose "Copy link" from the menu.
### How to Get Author Profile URLs 
It's pretty much the same process as getting addon URLs. Just right-click on the author's name link and select "Copy link."
