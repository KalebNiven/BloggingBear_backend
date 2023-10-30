from utilities import formulate_instructions, generate_content, create_google_doc, update_google_doc
from google_api import client, setup_google_docs_api
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import pandas as pd
from config import OPENAI_API_KEY
from cryptography.fernet import Fernet
from rq import Worker, Queue, get_current_job
from flask_sqlalchemy import SQLAlchemy
from redis import Redis
from rq.job import Job
import json

logging.basicConfig(level=logging.DEBUG)

#test commit

app = Flask(__name__)
# CORS(app)
# CORS(app, resources={r"/*": {"origins": "https://bloggingbear-frontend-39f0be1ffd81.herokuapp.com/"}})
CORS(app)
# Access the Redis URL provided by Heroku's environment variable
redis_url = os.environ.get("REDISCLOUD_URL")
redis_conn = Redis.from_url(redis_url)
# for local use
# redis_conn = Redis()
task_queue = Queue("task_queue", connection=redis_conn)

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


# Create another route to get the decrypted token
@app.route('/get_token', methods=['GET'])
def get_token():
    return "ug"
    # try: 
    #     # Get the encrypted token from your .env file
    #     with open(".env", "r") as env_file:
    #         for line in env_file:
    #             if line.startswith('USER_TOKEN='):
    #                 encrypted_token = line[len('USER_TOKEN='):-1]
    #
    #     # Decrypt the token
    #     decrypted_token = cipher_suite.decrypt(encrypted_token.encode())
    #     return jsonify({'token': decrypted_token.decode()}), 200
    # except Exception as e:
    #     return jsonify({'error': str(e)}), 400


def calculate_percentage(completed, total):
    if total == 0:
        return 0  # To avoid division by zero
    percentage = (completed / total) * 100
    return percentage


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
        # If there is an error (like a failure to fetch the data), log the error and return a 400 status code
        logging.exception("Failed to fetch spreadsheet data")
        return jsonify({'error': str(e)}), 400


@app.route('/get-doc-urls', methods=['GET'])
def get_doc_urls():
    try:
        return jsonify({'document_urls': doc_urls}), 200
    except Exception as e:
        logging.exception("Error in get-doc-urls endpoint")
        return jsonify({'error': str(e)}), 400


def generate_content_queue(data):
    job = get_current_job()
    logging.info("Received request at /generate-content endpoint")
    # try:
    # Get the payload from the request
    selected_rows = data.get('data')
    max_tokens = data.get('max_tokens', 150)  # Default to 150 if not provided
    folder_id = data.get('folder_id')
    if not selected_rows:
        return json.dumps({'error': "Data not provided"}), 400
    if not folder_id:
        return json.dumps({'error': "Folder Path not provided"}), 400

    logging.debug("Received data: %s", data)

    response_data = []
    for index, row in enumerate(selected_rows):
        row_data = []
        if 'Instructions' not in row:
            return json.dumps({'error': "Instructions not provided of row " + str(row.get('row_no'))}), 400
        if 'Blog Title' not in row:
            return json.dumps({'error': "Blog Title not provided of row " + str(row.get('row_no'))}), 400
        if len(row.get('Instructions')) < 1:
            return json.dumps({'error': "Instructions not provided of row " + str(row.get('row_no'))}), 400
        if len(row.get('Blog Title')) < 1:
            return json.dumps({'error': "Blog Title not provided of row " + str(row.get('row_no'))}), 400
        instructions = formulate_instructions(row, run_number=1)
        for no, instruction in enumerate(instructions):
            content = generate_content(OPENAI_API_KEY, instruction, max_tokens)
            if hasattr(content, 'json_body'):
                return json.dumps({'error': str(content.json_body.get('error').get('message')) + " on row " + str(
                    row.get('row_no'))}), 400
            else:
                try:
                    print("---content---")
                    print(content)
                    print("---content choices---")
                    print(content["choices"])
                    print("---content choices 0---")
                    print(content["choices"][0])
                    print("---content choices 0 message---")
                    print(content["choices"][0]["message"])
                    print("---content choices 0 message content---")
                    print(content["choices"][0]["message"]["content"])
                    row_data.append(content["choices"][0]["message"]["content"])
                    percentage_done = calculate_percentage(no + 1, len(instructions))
                    job.meta['status'] = 'in_progress'
                    job.meta["percentage_done"] = percentage_done
                    job.save()
                except Exception as e:
                    # "Data provided by gpt is not correct please send this row " + str(
                    #     row.get('row_no')) + " again"
                    return json.dumps(
                        {'error': str(e)}), 400
        rows = {
            "title": row['Blog Title'],
            "content": ''.join(row_data),
            "folder_id": folder_id,
        }
        response_data.append(rows)
        print("response data")
        print(response_data)

    # Return the generated content
    return create_doc(response_data)


@app.route('/generate-content', methods=['POST'])
def generate_content_endpoint():
    data = request.get_json()
    from App import generate_content_queue
    job = task_queue.enqueue_call(
        func=generate_content_queue, args=(data,), result_ttl=4000, timeout=1000
    )
    return jsonify({'task_id': job.get_id()}), 200


@app.route("/results/<job_key>", methods=['GET'])
def get_results(job_key):
    job = Job.fetch(job_key, connection=redis_conn)
    job.refresh()
    if job.is_finished:
        if isinstance(job.result, str):
            return jsonify(json.loads(job.result)), 200
        else:
            error_message, status_code = job.result
            # Convert the response dictionary to a JSON string
            return jsonify(json.loads(error_message)), status_code
    else:
        if job.meta:
            if job.meta.get("status") == "in_progress":
                return jsonify({"status": "In Progress",
                                "percentage_done": str(job.meta.get("percentage_done"))}), 200
        else:
            return jsonify({"status": "In Progress", "percentage_done": str(0)}
                           ), 200


def create_doc(data):
    try:
        print("in doc function")
        doc_name = []
        for row in data:
            title = row.get('title')
            folder_id = row.get('folder_id')
            content = row.get('content')
            # Create a new Google Doc using the function you defined earlier
            doc_id, name = create_google_doc(title, folder_id)
            doc_name.append(name)
            # Log the successful creation
            logging.info("Document created successfully")

            # Update the Google Doc with the content using the function you defined earlier
            update_google_doc(doc_id, content)

        # log the successful update
        logging.info("Document updated successfully")
    except Exception as e:
        return json.dumps({'error': "Data not provided"}), 400

    # Return the doc ID and URL
    return json.dumps({'docId': "Document created successfully " + ''.join(doc_name),
                       'status': "Completed",
                       'docurl': "https://docs.google.com/document/d/" + str(doc_id) + "/edit"})


if __name__ == '__main__':
    # setup_google_docs_api()
    app.run(debug=False, host="0.0.0.0")
