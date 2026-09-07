import os
from dotenv import load_dotenv
from tavily import TavilyClient


# Load environment variables
load_dotenv()

# Get Tavily API key
api_key = os.getenv("TAVILY_API_KEY")

if not api_key:
    raise ValueError("TAVILY_API_KEY not found in .env file")

# Create Tavily client
tavily = TavilyClient(api_key=api_key)


def search_company(company_name):
    """
    Search the web for information about a company.
    """

    response = tavily.search(
        query=f"{company_name} company business model funding market competitors",
        search_depth="advanced",
        max_results=5
    )

    return response


# Test the search
if __name__ == "__main__":

    company = input("Enter company name: ")

    print(f"\nSearching for {company}...\n")

    results = search_company(company)

    for result in results["results"]:

        print("=" * 70)

        print("TITLE:")
        print(result["title"])

        print("\nURL:")
        print(result["url"])

        print("\nCONTENT:")
        print(result["content"])

        print()