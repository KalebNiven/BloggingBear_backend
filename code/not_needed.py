@app.route('/execute-script', methods=['POST'])
def execute_script():
    try:
        data = request.get_json()
        api_key = data.get('api_key')
        sheet_url = data.get('sheetUrl')
        sheet_name = data.get('sheetName')

        result = main(api_key, sheet_url, sheet_name)
        return jsonify({'message': result}), 200
    except Exception as e:
        logging.exception("Error in execute-script endpoint")
        return jsonify({'error': str(e)}), 500
   
@app.route('/start-script', methods=['POST'])
def start_script():
    logging.info("Received request at /start-script endpoint")
    try:
        data = request.get_json()
        api_key = data.get('api_key')
        sheet_url = data.get('sheetUrl')
        sheet_name = data.get('sheetName')

        main(api_key, sheet_url, sheet_name)
        return jsonify({'message': 'Script completed successfully'}), 200
    except Exception as e:
        logging.exception("Error in start-script endpoint")
        return jsonify({'error': str(e)}), 500
  