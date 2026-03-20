import os
from dotenv import load_dotenv

env_file = '.env.dev' if os.getenv('STAGE') == 'dev' else '.env.prod'
load_dotenv(dotenv_path=env_file)

BOT_TOKEN = os.getenv('BOT_TOKEN')
WORDLE_BOT_ID = int(os.getenv('WORDLE_BOT_ID', '0'))
