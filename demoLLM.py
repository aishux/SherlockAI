from langchain_openai import AzureChatOpenAI

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT = "https://aishu-m8q3ed4m-swedencentral.cognitiveservices.azure.com/"
AZURE_OPENAI_KEY = "028qDuTdd4Z5y0nsdbVns8ZesZeQxt4NEQmW33BObOs7cLO9gIteJQQJ99BCACfhMk5XJ3w3AAAAACOGWE1L"
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