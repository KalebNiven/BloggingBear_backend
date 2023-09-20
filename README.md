# BloggingBear

This is the Python backend content generator that facilitates the automatic creation of content documents using data from Google spreadsheets. Below is a guide to setting up, using, and understanding the structure of this project.


### Prerequisites

- Python 3.x
- Node.js and npm (for the frontend)
- Flask
- Pandas
- Google API client library
- Cryptography package
- Flask-CORS

You'll need to have a Google APIs client ID and secret, OpenAI API key, and be logged in to the Google Cloud console.



### Backend Setup

Navigate to the `backend/` directory and set up a Python virtual environment:

```sh
python3 -m venv venv
```

Activate the virtual environment:

```sh
source venv/bin/activate # On Windows use: .\venv\Scripts\activate
```

Install the required Python packages:

```sh
pip install -r requirements.txt
```

(You will need to create a `requirements.txt` file containing all the necessary Python packages.)

Setup your environment variables in a `.env` file in the `backend/` directory. Your `.env` file should look something like this:

```sh
OPENAI_API_KEY=your_openai_api_key
```

### Running the Backend Server

Ensure that you are in the `backend/` directory and your virtual environment is activated. Run the Flask server using the following command:

```sh
python App.py
```

The server will start on `http://localhost:5000/`.

### Endpoints

Your backend server exposes several endpoints, which are described below:

- **POST /google-auth**
  - Authenticate with Google OAuth.
  - Payload: `token` (string), `client_id` (string)
  
- **GET /get_token**
  - Retrieves the decrypted token.

- **POST /upload-file**
  - Uploads a file for processing.
  - Payload: A form-data with the 'file' field containing the file to be uploaded.

- **GET /get-spreadsheet-data**
  - Retrieves data from a Google Spreadsheet.
  - Parameters: `sheetUrl` (string)

- **GET /get-doc-urls**
  - Retrieves the URLs of the generated Google docs.

- **POST /generate-content**
  - Generates content based on the given data.
  - Payload: `data` (array), `max_tokens` (integer, optional)

- **POST /create-doc**
  - Creates and populates a Google Doc with the generated content.
  - Payload: `title` (string), `content` (string), `email` (string)

### Usage

Provide detailed steps for using your application, including how to use the frontend to interact with the backend server, and how the endpoints can be used to perform different tasks, such as uploading files, generating content, and creating Google Docs.


"# BloggingBear" 
"# BloggingBear_backend" 
