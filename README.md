## Setup Instructions

### Prerequisites

* Python 3.10 or higher
* Poetry (Python dependency management tool)
* A Google API Key with access to the Generative Language API (Gemini models).

### Steps

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/vaibhavrohilla-03/webscraping_ragchatbot.git
    cd webscraping_ragchatbot
    ```

2.  **Install Poetry:**
    If you don't have Poetry installed, follow the instructions on the [official Poetry website](https://python-poetry.org/docs/#installation).

3.  **Create `.env` File:**
    Create a file named `.env` in the root directory of the project and add your Google API key:
    ```env
    GOOGLE_API_KEY="your_actual_google_api_key_here"
    ```
    This file will be used by the application to access Google AI services.

4.  **Install Dependencies:**
    Navigate to the project root and let Poetry install the dependencies from pyproject.toml or poetry.lock
    ```bash
    poetry install --only main
    ```

5.  **Run the Chatbot Application:**
    Once the knowledge base has been successfully prepared, you can run the chatbot:
    ```bash
    poetry run streamlit run app/chatbot.py
    ```
    
6.  **Prepare the Knowledge Base:**
    In the Streamlit interface that opens:
    * Enter the website URL you want to process.
    * Click the "Prepare Knowledge Base" button.
    This process will scrape the website, split the content, create embeddings, and store them in a ChromaDB vector database within the `Data/` directory.

### I have included a dockerfile too to run this locally
