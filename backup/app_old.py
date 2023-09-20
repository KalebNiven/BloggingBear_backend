from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import time
import json
import gspread
import openai
import pickle
from oauth2client.service_account import ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

app = Flask(__name__)
CORS(app)


# Define your constants
OPENAI_API_KEY = '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'
SHEETS_CREDENTIALS_PATH = 'job-scraping-key.json'
DOCS_CREDENTIALS_PATH = 'client_secret_quartzWhitpser.json'
SHEET_NAME = 'Sheet1'
SHEET_URL = 'https://docs.google.com/spreadsheets/d/1-ClO6AKnuK1Sb_l648FsUHxAjxdzXoJphI3OYGhZC9g/edit#gid=0'

# Define global variables
doc_urls = []

# Set up Google Sheets API
scope = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
credentials = ServiceAccountCredentials.from_json_keyfile_name(SHEETS_CREDENTIALS_PATH, scope)
client = gspread.authorize(credentials)

# Set up OpenAI API
openai.api_key = OPENAI_API_KEY


# Define your get_row_ranges, get_all_values, and other helper functions here

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/start-script', methods=['POST'])
def start_script():
    try:
        data = request.get_json()  # Parse JSON request data if applicable
        api_key = data.get('api_key')  # Access data elements as needed
        
        # Adapt your code here
        main(api_key)  # Call your 'main' function with request data
        return jsonify({'message': 'Script completed successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get-doc-urls', methods=['GET'])
def get_doc_urls():
    # Implement logic to retrieve document URLs
    # Return a JSON response with the document URLs
    # This route can be used to fetch the document URLs if needed
    return jsonify({'document_urls': doc_urls}), 200

@app.route('/execute-script', methods=['POST'])
def execute_script():
    try:
        data = request.get_json()  # Parse JSON request data
        api_key = data.get('apiKey')
        sheet_url = data.get('sheetUrl')
        sheet_name = data.get('sheetName')
        
        # Call the script function with the provided data
        result = run_script(api_key, sheet_url, sheet_name)
        
        # Return a response with the result
        return jsonify({'message': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def run_script(api_key, sheet_url, sheet_name):
    try:
        # Step 1: Setup Google Sheets API and fetch the data
        client = gspread.authorize(credentials)
        spreadsheet = client.open_by_url(sheet_url)
        worksheet = spreadsheet.worksheet(sheet_name)
        sheet_data = worksheet.get_all_records()

        # Step 2: Process the data using OpenAI API
        for row in sheet_data:
            # Assume 'prompt1', 'prompt2', 'prompt3' are columns in your sheet
            prompt1 = row.get('prompt1')  # Replace with your actual column name
            prompt2 = row.get('prompt2')  # Replace with your actual column name
            prompt3 = row.get('prompt3')  # Replace with your actual column name

            # Make OpenAI API calls with these prompts and store the responses
            response1 = openai.Completion.create(engine="davinci", prompt=prompt1, max_tokens=150, api_key=api_key)
            response2 = openai.Completion.create(engine="davinci", prompt=prompt2, max_tokens=150, api_key=api_key)
            response3 = openai.Completion.create(engine="davinci", prompt=prompt3, max_tokens=150, api_key=api_key)

            # Step 3: Create a new Google Doc with the responses
            # Here we create a new Google Doc and write the responses to it
            # I'm using 'docs' to represent the Google Docs service you'll set up
            docs = build('docs', 'v1', credentials=credentials)  # You'll need to set up OAuth 2.0 credentials for this
            doc = docs.documents().create(body={
                'title': 'Generated Doc for Row {}'.format(row)  # Give your doc a title
            }).execute()
            doc_id = doc['documentId']

            # Add the responses to the Google Doc
            requests = [
                {'insertText': {'location': {'index': 1}, 'text': "Response 1: {}\n".format(response1['choices'][0]['text'])}},
                {'insertText': {'location': {'index': 1}, 'text': "Response 2: {}\n".format(response2['choices'][0]['text'])}},
                {'insertText': {'location': {'index': 1}, 'text': "Response 3: {}\n".format(response3['choices'][0]['text'])}},
            ]
            docs.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
            
            # Save the document URLs to a global list
            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
            doc_urls.append(doc_url)

        return 'Script executed successfully'
    except Exception as e:
        return f'Error: {str(e)}'



def main(api_key, sheet_url, sheet_name):
    # Modify your 'main' function to accept 'api_key', 'sheet_url', and 'sheet_name' as parameters
    # Your existing 'main' function code here





if __name__ == '__main__':
    app.run(debug=True)
