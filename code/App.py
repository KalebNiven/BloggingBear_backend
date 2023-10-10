from utilities import formulate_instructions, generate_content, create_google_doc, update_google_doc
from google_api import client, setup_google_docs_api
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import pandas as pd
from config import cipher_suite, OPENAI_API_KEY
from cryptography.fernet import Fernet

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

# Attempt to load the secret key from an environment variable
# If it doesn't exist, create a new one and save it in the environment variable
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    secret_key = Fernet.generate_key().decode()
    os.environ['SECRET_KEY'] = secret_key

# Make sure to set your secret key
app.secret_key = secret_key

# Initialize cipher suite
cipher_suite = Fernet(secret_key.encode())

# Initialize an empty list to store doc URLs
doc_urls = []


# @app.route('/google-auth', methods=['POST'])
# def google_auth():
#
#     try:
#         # Get the token sent by the frontend
#         token = request.json['token']
#         client_id = request.json['client_id']
#
#         # Verify the token
#         idinfo = id_token.verify_oauth2_token(token, requests.Request(), client_id)
#
#         # ID token is valid, get the user's info
#         userid = idinfo['sub']
#         email = idinfo['email']
#
#         # Creating a session
#         session['user_id'] = userid
#         session['email'] = email
#
#         # Encrypt the token and save it to your .env file
#         encrypted_token = cipher_suite.encrypt(token.encode())
#         with open(".env", "a") as env_file:
#             env_file.write(f"\nUSER_TOKEN={encrypted_token.decode()}")
#
#
#     except ValueError:
#         print("Invalid token")
#         # Invalid token
#         return jsonify(message="Invalid token"), 401
#     except Exception as e:
#         # Catch any other exceptions
#         return jsonify(message=str(e)), 500
#
#
#
#     # ... (further processing: create session, etc.)
#     return jsonify(message="Successfully authenticated", email=email)


# Create another route to get the decrypted token
@app.route('/get_token', methods=['GET'])
def get_token():
    try:
        # Get the encrypted token from your .env file
        with open(".env", "r") as env_file:
            for line in env_file:
                if line.startswith('USER_TOKEN='):
                    encrypted_token = line[len('USER_TOKEN='):-1]

        # Decrypt the token
        decrypted_token = cipher_suite.decrypt(encrypted_token.encode())
        return jsonify({'token': decrypted_token.decode()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/upload-file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filepath = os.path.join('uploads', file.filename)
    file.save(filepath)

    # Read and process the file using pandas (step 2)
    data = pd.read_csv(filepath)  # Adjust based on your file type (e.g., pd.read_excel for Excel files)
    data_json = data.to_json(orient='records')

    return jsonify({'message': 'File uploaded successfully'}), 200


#
@app.route('/get-spreadsheet-data', methods=['POST'])
def get_spreadsheet_data():
    sheet_url = request.json['sheet_url']
    # sheet_url = "https://docs.google.com/spreadsheets/d/1rAvTLKjabmti9tNLF5uO9dF-jphi4D1v_pODV0h_g7E/htmlembed"

    try:
        # Logic to fetch and return data from the spreadsheet using the sheet_url
        spreadsheet = client.open_by_url(sheet_url)
        worksheet = spreadsheet.get_worksheet(0)  # Assuming data is in the first worksheet
        data = worksheet.get_all_records()  # Getting all the data as a list of dictionaries

        # Log the successful data retrieval
        logging.info("Data retrieved successfully")

        return jsonify({'message': 'Data retrieved successfully', 'data': data}), 200
    except Exception as e:
        # If there is an error (like a failure to fetch the data), log the error and return a 500 status code
        logging.exception("Failed to fetch spreadsheet data")
        return jsonify({'error': str(e)}), 500


@app.route('/get-doc-urls', methods=['GET'])
def get_doc_urls():
    try:
        return jsonify({'document_urls': doc_urls}), 200
    except Exception as e:
        logging.exception("Error in get-doc-urls endpoint")
        return jsonify({'error': str(e)}), 500


@app.route('/generate-content', methods=['POST'])
def generate_content_endpoint():
    logging.info("Received request at /generate-content endpoint")
    # try:
    # Get the payload from the request
    data = request.get_json()
    selected_rows = data.get('data')
    max_tokens = data.get('max_tokens', 150)  # Default to 150 if not provided
    folder_id = data.get('folder_id')
    if not selected_rows:
        return jsonify({'error': "Data not provided"}), 500
    if not folder_id:
        return jsonify({'error': "Folder Path not provided"}), 500

    logging.debug("Received data: %s", data)

    # The following is a loop that goes through each selected row,
    # formulates instructions, and then generates content using your existing function.
    # Note that the `formulate_instructions` function is called with a made-up `run_number` argument.
    # You might need to adjust this part to correctly derive the run_number from your data or API request.
    response_data = []
    for index, row in enumerate(selected_rows):
        row_data = []
        if 'Instructions' not in row:
            return jsonify({'error': "Instructions not provided of row " + str(row.get('row_no'))}), 500
        if 'Blog Title' not in row:
            return jsonify({'error': "Blog Title not provided of row " + str(row.get('row_no'))}), 500
        instructions = formulate_instructions(row, run_number=1)
        for instruction in instructions:
            content = generate_content(OPENAI_API_KEY, instruction, max_tokens)
            if hasattr(content, 'json_body'):
                return jsonify({'error': str(content.json_body.get('error').get('message')) + " on row " + str(
                    row.get('row_no'))}), 500
            else:
                row_data.append(content.get('choices')[0].get('message').get('content'))
        rows = {
            "title": row['Blog Title'],
            "content": ''.join(row_data),
            "folder_id": folder_id,
        }
        response_data.append(rows)

    # Return the generated content
    return create_doc(response_data)
    # return jsonify({'data': response_data}), 200


# except Exception as e:
#     # Handle any errors that occur
#     logging.error("An error occurred: %s", str(e))
#     return jsonify({'error': str(e)}), 500


def create_doc(data):
    try:
        doc_name = []
        for row in data:
            title = row.get('title')
            folder_id = row.get('folder_id')
            content = row.get('content')
            # Create a new Google Doc using the function you defined earlier
            doc_id, name = create_google_doc(title, folder_id)
            doc_name.append("," + name)
            # Log the successful creation
            logging.info("Document created successfully")

            # Update the Google Doc with the content using the function you defined earlier
            update_google_doc(doc_id, content)

        # log the successful update
        logging.info("Document updated successfully")
    except KeyError as e:
        return jsonify({'error': "Data not provided"}), 500
    except Exception as e:
        return jsonify(error=str(e), message="An error occurred"), 500

    # Return the doc ID and URL
    return jsonify({'docId': "Document created successfully " + ''.join(doc_name)})


# def main(api_key, sheet_url, sheet_name):
#     logging.info("Starting the main function")
#     doc_urls = []
#
#
#     try:
#         logging.info("Setting up Google Sheets API")
#         # Ensure credentials are defined before this line
#         # client = gspread.authorize(credentials)
#         logging.info("Fetching sheet data")
#         spreadsheet = client.open_by_url(sheet_url)
#         worksheet = spreadsheet.worksheet(sheet_name)
#         sheet_data = worksheet.get_all_records()
#
#          # Define column pairs for each run
#         column_pairs = [
#             ('Headline_1', 'Keywords_1'),
#             ('Headline_2', 'Keywords_2'),
#             ('Headline_3', 'Keywords_3'),
#             ('Headline_4', 'Keywords_4'),
#             ('Headline_5', 'Keywords_5'),
#         ]
#
#         for row in sheet_data:
#             blog_title = row.get('Blog Title')
#
#             doc_id, doc_url = create_google_doc(blog_title)
#
#             # Ensure that the first three runs have data
#             for i in range(3):
#                 if not row.get(column_pairs[i][0]) or not row.get(column_pairs[i][1]):
#                     raise ValueError(f"Data missing for mandatory run number {i+1}")
#
#             for run_number, (headline_col, keywords_col) in enumerate(column_pairs, start=1):
#                 headline = row.get(headline_col)
#                 keywords = row.get(keywords_col)
#
#                 # Check if data is present in both cells
#                 if headline and keywords:
#                     # Formulate instructions and generate content
#                     instructions = formulate_instructions(row, run_number)
#                     content = generate_content(api_key, instructions, max_tokens=550)
#
#                     # Update the Google Doc with the generated content
#                     update_google_doc(doc_id, content.choices[0].message['content'])
#                 else:
#                     # Break if any cell is empty
#                     break
#
#             doc_urls.append(doc_url)
#
#         return 'Script executed successfully'
#     except Exception as e:
#             logging.exception("Error in main function")
#             return f'Error: {str(e)}'


if __name__ == '__main__':
    # setup_google_docs_api()
    app.run(debug=False)
