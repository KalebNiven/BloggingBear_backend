from dotenv import load_dotenv
import os
from cryptography.fernet import Fernet
load_dotenv()

# Generate a key and instantiate a Fernet instance
key = Fernet.generate_key()
cipher_suite = Fernet(key)

def get_env_variable(var_name):
    var_value = os.getenv(var_name)
    if not var_value:
        raise EnvironmentError(f"{var_name} is not set in the .env file")
    return var_value

# Loading environment variables
OPENAI_API_KEY = get_env_variable("OPENAI_API_KEY")
CORS_ORGINS = get_env_variable("CORS_ORGINS")
