import os
import requests
import json
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

load_dotenv(encoding='utf-16')

# Monday.com API credentials
MONDAY_API_URL = "https://api.monday.com/v2"
MONDAY_API_KEY = os.getenv('MONDAY_API_KEY')
BOARD_ID = os.getenv('BOARD_ID')

# SendGrid API credentials
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
FROM_EMAIL = os.getenv('FROM_EMAIL')

# Check if all required environment variables are set
required_vars = ['MONDAY_API_KEY', 'BOARD_ID', 'SENDGRID_API_KEY', 'FROM_EMAIL']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Query to fetch items using the correct structure
query = f'''
query {{
  boards(ids: {BOARD_ID}) {{
    items_page(limit: 500) {{
      items {{
        name
        column_values(ids: ["email1__1", "email_content__1"]) {{
          id
          text
        }}
      }}
    }}
  }}
}}
'''

def fetch_monday_data(query):
    headers = {
        "Authorization": MONDAY_API_KEY,
        "Content-Type": "application/json",
    }
    
    data = {"query": query}
    
    response = requests.post(url=MONDAY_API_URL, json=data, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed to run with a {response.status_code} error. {response.text}")

def send_email(to_email, content):
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to_email,
        subject='Your Email from Monday Board',
        plain_text_content=content)
    
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email sent to {to_email}. Status Code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error sending email to {to_email}: {str(e)}")
        return False

def main():
    try:
        # Fetch items from Monday.com
        response_data = fetch_monday_data(query)
        
        # Check if 'data' key exists in the response
        if 'data' not in response_data:
            print("Error: 'data' key not found in the API response.")
            return
        
        # Navigate through the response structure
        boards = response_data['data']['boards']
        if not boards:
            print("Error: No boards found in the response.")
            return
        
        items_page = boards[0]['items_page']
        if 'items' not in items_page:
            print("Error: No items found on the board.")
            return
        
        # Process items and send emails
        items = items_page['items']
        for item in items:
            name = item['name']
            email = next((cv['text'] for cv in item['column_values'] if cv['id'] == 'email1__1'), None)
            content = next((cv['text'] for cv in item['column_values'] if cv['id'] == 'email_content__1'), None)
            
            if email and content:
                print(f"Sending email to {name} at {email}")
                if send_email(email, content):
                    print(f"Email sent successfully to {name}")
                else:
                    print(f"Failed to send email to {name}")
            else:
                print(f"Skipping {name} due to missing email or content")
            
            print("---")
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()