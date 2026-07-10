from dotenv import load_dotenv
import os

from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference

load_dotenv()

credentials = Credentials(
    url=os.getenv("IBM_URL"),
    api_key=os.getenv("IBM_API_KEY"),
)

model = ModelInference(
    model_id="meta-llama/llama-3-3-70b-instruct",
    credentials=credentials,
    project_id=os.getenv("IBM_PROJECT_ID"),
)

try:
    response = model.generate_text(
        prompt="Say only Hello",
        params={
            "max_new_tokens": 20
        }
    )

    print(response)

except Exception as e:
    import traceback
    traceback.print_exc()