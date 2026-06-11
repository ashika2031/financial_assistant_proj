# AWS Bedrock Fallback Integration

This project uses **AWS Bedrock** as the secondary cloud LLM, providing
resilience if Vertex AI is unavailable or unauthenticated.

## 1. Prerequisites

- An AWS account with access to Amazon Bedrock enabled in your region
- Model access granted for **Anthropic Claude 3 Sonnet**
  (`anthropic.claude-3-sonnet-20240229-v1:0`) in the Bedrock console under
  "Model access"
- AWS credentials configured (same credentials used for SageMaker / boto3)

## 2. Configure environment variables

In `.env`:

```
AWS_DEFAULT_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

## 3. How it's wired into the chatbot

`app/chatbot_router.py` defines `_call_bedrock(prompt)`:

```python
import boto3, json
from app.config import AWS_REGION, BEDROCK_MODEL_ID

def _call_bedrock(prompt: str) -> str:
    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "messages": [{"role": "user", "content": prompt}],
    }
    response = client.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=json.dumps(body),
    )
    payload = json.loads(response["body"].read())
    return payload["content"][0]["text"]
```

`get_answer()` calls `_call_vertex()` first; if that raises (missing
credentials, network error, quota), it calls `_call_bedrock()`. If that
also fails, it falls back to `_rule_based_summary()`.

## 4. Testing the Bedrock integration directly

```bash
python -c "
from app.chatbot_router import _call_bedrock
print(_call_bedrock('Summarize: Prologis reported \$2.1B revenue in Q4 2023.'))
"
```

## 5. Alternative: Azure OpenAI

If you prefer Azure OpenAI instead of Bedrock as the secondary provider,
swap `_call_bedrock()` for an Azure OpenAI call:

```python
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-15-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)

def _call_azure_openai(prompt: str) -> str:
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
    )
    return response.choices[0].message.content
```

Add the corresponding variables to `.env`:

```
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
```

and call `_call_azure_openai()` in place of `_call_bedrock()` inside
`get_answer()`'s fallback chain.
