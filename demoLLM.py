from langchain.chat_models import AzureChatOpenAI
from langchain.schema import HumanMessage

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT = "https://aishu-m8m23xc2-eastus2.cognitiveservices.azure.com/"
AZURE_OPENAI_KEY = "2TpUnxlwFmgMU5xCyFc4HncL43stei4En4SRL6KbD6oH5062zE7hJQQJ99BCACHYHv6XJ3w3AAAAACOGWq6g"
AZURE_DEPLOYMENT_NAME = "gpt-4o"

# Initialize the Azure Chat Model in LangChain
llm = AzureChatOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    openai_api_version="2025-01-01-preview",
    azure_deployment=AZURE_DEPLOYMENT_NAME,
    api_key=AZURE_OPENAI_KEY,
)

# Send Message
response = llm.invoke("Hello, Azure AI!")
print(response)