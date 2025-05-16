
# Webscraping RAGBOT
This project is a Retrieval Augmented Generation (RAG) application designed to answer questions based on information scraped from lets say a university website or any website. It uses a vector database to store website content and a Large Language Model (LLM) to generate answers. The application is built with Python, Langchain, Streamlit, and uses Google Generative AI for embeddings and chat functionalities.

## Setup Instructions

You can set up and run this project either locally using Poetry or via Docker.

### Setup

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/vaibhavrohilla-03/webscraping_ragchatbot.git

2.  **Create `.env` File:**
    Create a file named `.env` in the root directory of the project and add your Google API key:
    ```env
    GOOGLE_API_KEY="your_actual_google_api_key_here"
    ```
    This file will be used by the `docker run` command.

3.  **Build the Docker Image:**
    From the project root directory (where the `Dockerfile` is located):
    ```bash
    docker build -t webscraping_ragchatbot .
    ```

4.  **Run the Docker Container:**

    * **To run the Chatbot application (default):**
        To persist the `Data` directory (containing `scraped_data.jsonl` and `chroma_db`) on your host machine, create a `Data` folder in your project root if it doesn't exist, and then run:
        ```bash
        # docker run -p 8501:8501 --env-file .env -v "%cd%/Data:/app/Data" webscraping_ragchatbot
        ```
