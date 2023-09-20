import openai
import os

def formulate_instructions(row_data, run_number):
    """
    Formulates the instructions for content generation based on the data from a specific row in the Google Sheet.
    """

    # Mapping of run numbers to the corresponding column names for headlines and keywords
    column_map = {
        1: ('Headlines_1', 'Keywords_1'),  # Columns 'D' and 'E'
        2: ('Headlines_2', 'Keywords_2'),  # Columns 'F' and 'G'
        3: ('Headlines_3', 'Keywords_3'),  # Columns 'H' and 'I'
        # Add more mappings for further runs if needed
    }

    # Fetching the correct column names based on the run number
    headlines_col, keywords_col = column_map.get(run_number, ('Headlines_1', 'Keywords_1'))

    # Use the data from 'row_data' to construct your instruction template
    style = row_data['Instructions']  # Column 'C' 
    title = row_data['Blog Title']  # Column 'A' 
    headlines = row_data[headlines_col]
    keywords = row_data[keywords_col]
    additional_data = ""
    if row_data['Facts'] is not None:
        additional_data = row_data['Facts']  # Column 'N' 
    


    # Constructing the core instruction
    instruction = (
        f"Today, you are writing in the following style: '{style}'\n\n"
        f"So, keeping in mind this style, I want you to write a few sections for a blog titled: '{title}'\n\n"
        f"Please write about the following (keep titles the same even though they are boring). Please write concise, straight-to-the-point content for the topics in the subheadlines, directly answering any questions they pose. No intros or outros unless directed. Maintain the headline formats (H2, H3, etc.) and continuously relate the content back to the main blog title. Ensure the content is the user needs focused and avoids any 'mumbling.' Here are the headlines to write about: '{headlines}'\n\n"
        f"Please use the following keywords (no need to make it bold): '{keywords}'"
    )

    # Adding the additional data instruction for the first run
    if run_number == 1 and additional_data:
        instruction += (
            f"\n\nPlease also integrate additional data into to the post to show your authority and understanding of the subject. Please ensure that hyperlinks are tucked right into the text so your readers can click away to learn more without stumbling upon footnotes. The anchor texts have to be facts and figures. The data with sources are the following: “{additional_data}'"
        )
    
    return instruction

def generate_content(openai_api_key, instructions, max_tokens=550):
    """
    Generates content using the OpenAI API.
    """
    openai.api_key = openai_api_key
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0301", 
            messages=[
                {"role": "system", "content": 'You are a kick-ass writer who can write in absolutely any style and about any subject. And you are about to write a blog post.'},
                {"role": "user", "content": instructions}
            ], 
            max_tokens=max_tokens
        )
        return response
    except Exception as e:
        print(f"Error in content generation: {e}")
        import traceback
        traceback.print_exc()  # This will print the full exception trace
        return None

def create_google_doc(doc_title, user_email):
    global docs_service
    doc = docs_service.documents().create(body={'title': doc_title}).execute()
    doc_id = doc['documentId']
    doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"

    # Share the document with the signed-in user
    permissions = {
        'role': 'writer',
        'type': 'user',
        'emailAddress': user_email,
    }
    docs_service.permissions().create(
        fileId=doc_id,
        body=permissions,
        fields='id',
    ).execute()

    return doc_id, doc_url


def update_google_doc(doc_id, content):
    global docs_service
    requests = [
        {
            'insertText': {
                'location': {
                    'index': 1
                },
                'text': content
            }
        }
    ]
    docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()


