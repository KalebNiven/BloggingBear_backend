import pickle
import os
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import service_account
import gspread

# from code.App import cipher_suite

# Define paths and scopes
SHEETS_CREDENTIALS_PATH = 'json/job-scraping-key.json'
DOCS_CREDENTIALS_PATH = 'json/sheet.json'

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'

]

# Authenticate and build services
creds = service_account.Credentials.from_service_account_file(SHEETS_CREDENTIALS_PATH, scopes=SCOPES)
docs_service = build('docs', 'v1', credentials=creds)

client = gspread.authorize(creds)

def setup_google_docs_api():
    """
    Set up the Google Docs API by initializing the global `docs_service` variable.

    This function checks if the `token.pickle` file exists. If it does, it loads the credentials
    from the file. If the credentials are not valid, expired, or there is no refresh token,
    it initiates the authentication flow and runs a local server to obtain new credentials.
    After obtaining the credentials, it saves them to the `token.pickle` file for future use.

    """
    # Authenticate using the credentials file
    credentials_file = "json/job-scraping-key.json"
    credentials = service_account.Credentials.from_service_account_file(credentials_file, scopes=[
        'https://www.googleapis.com/auth/drive'])
    # Create a Google Drive API service
    global drive_service
    drive_service = build('drive', 'v3', credentials=credentials)
    global docs_service
    creds = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(DOCS_CREDENTIALS_PATH, SCOPES)
            creds = service_account.Credentials.from_service_account_file(SHEETS_CREDENTIALS_PATH, scopes=SCOPES)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    docs_service = build('docs', 'v1', credentials=creds)

def get_decrypted_token():
    encrypted_token = os.getenv('USER_TOKEN')
    if not encrypted_token:
        raise ValueError("Token is not set in the .env file")

    decrypted_token = cipher_suite.decrypt(encrypted_token.encode())
    return decrypted_token.decode()