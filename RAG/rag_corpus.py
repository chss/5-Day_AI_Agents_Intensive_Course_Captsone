# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.auth import default
from google.api_core.exceptions import ResourceExhausted
import vertexai
from vertexai.preview import rag
import os
from dotenv import load_dotenv, set_key
import requests
import tempfile

# Load environment variables from .env file
load_dotenv()

# --- Please fill in your configurations ---
# Retrieve the PROJECT_ID from the environmental variables.
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
if not PROJECT_ID:
    raise ValueError(
        "GOOGLE_CLOUD_PROJECT environment variable not set. Please set it in your .env file."
    )
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
if not LOCATION:
    raise ValueError(
        "GOOGLE_CLOUD_LOCATION environment variable not set. Please set it in your .env file."
    )
CORPUS_DISPLAY_NAME = "Signia"
CORPUS_DESCRIPTION = "Signia Stapler Information Corpus"
ENV_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


# --- Start of the script ---
def initialize_vertex_ai():
  credentials, _ = default()
  vertexai.init(
      project=PROJECT_ID, location=LOCATION, credentials=credentials
  )


def create_or_get_corpus():
  """Creates a new corpus or retrieves an existing one."""
  embedding_model_config = rag.EmbeddingModelConfig(
      publisher_model="publishers/google/models/text-embedding-004"
  )
  existing_corpora = rag.list_corpora()
  corpus = None
  for existing_corpus in existing_corpora:
    if existing_corpus.display_name == CORPUS_DISPLAY_NAME:
      corpus = existing_corpus
      print(f"Found existing corpus with display name '{CORPUS_DISPLAY_NAME}'")
      break
  if corpus is None:
    corpus = rag.create_corpus(
        display_name=CORPUS_DISPLAY_NAME,
        description=CORPUS_DESCRIPTION,
        embedding_model_config=embedding_model_config,
    )
    print(f"Created new corpus with display name '{CORPUS_DISPLAY_NAME}'")
  return corpus


def upload_pdf_to_corpus(corpus_name, pdf_path, display_name, description):
  """Uploads a PDF file to the specified corpus."""
  print(f"Uploading {display_name} to corpus...")
  try:
    rag_file = rag.upload_file(
        corpus_name=corpus_name,
        path=pdf_path,
        display_name=display_name,
        description=description,
    )
    print(f"Successfully uploaded {display_name} to corpus")
    return rag_file
  except ResourceExhausted as e:
    print(f"Error uploading file {display_name}: {e}")
    print("\nThis error suggests that you have exceeded the API quota for the embedding model.")
    print("This is common for new Google Cloud projects.")
    print("Please see the 'Troubleshooting' section in the README.md for instructions on how to request a quota increase.")
    return None
  except Exception as e:
    print(f"Error uploading file {display_name}: {e}")
    return None

def update_env_file(corpus_name, env_file_path):
    """Updates the .env file with the corpus name."""
    try:
        set_key(env_file_path, "RAG_CORPUS", corpus_name)
        print(f"Updated RAG_CORPUS in {env_file_path} to {corpus_name}")
    except Exception as e:
        print(f"Error updating .env file: {e}")

def list_corpus_files(corpus_name):
  """Lists files in the specified corpus."""
  files = list(rag.list_files(corpus_name=corpus_name))
  print(f"Total files in corpus: {len(files)}")
  for file in files:
    print(f"File: {file.display_name} - {file.name}")


def get_file_paths_in_folder(folder_path):
    """
    Returns a list of absolute file paths within the specified folder.

    Args:
        folder_path (str): The path to the folder.

    Returns:
        list: A list of strings, where each string is the absolute path to a file.
    """
    file_paths = []
    try:
        # List all entries in the directory
        for entry in os.listdir(folder_path):
            # Construct the full path of the entry
            full_path = os.path.join(folder_path, entry)
            # Define the path for the tracking file
            track_file = os.path.join(folder_path, "track_file.txt")
        
            # Check if the entry is a file
            if os.path.isfile(full_path):
                # Check if the track file is already tracked
                if os.path.isfile(track_file):
                    # Read the existing tracked files
                    with open(track_file, "r") as file:
                        lines = file.readlines()
                        # Check if the current file is already loaded
                        if os.path.abspath(full_path) + "\n" in lines:
                            print(f"File {os.path.abspath(full_path)} already tracked. Skipping.")
                        else:
                            # Append the new file to the tracking file
                            with open(track_file, "a") as file:
                                file.write(os.path.abspath(full_path) + "\n")
                            # Add the file path to the list
                            file_paths.append(os.path.abspath(full_path))
                else:        
                    # Create the tracking file and add the current file
                    with open(track_file, "w") as file:
                        file.write(os.path.abspath(full_path) + "\n")
                    file_paths.append(os.path.abspath(full_path))


    except FileNotFoundError:
        print(f"Error: The folder '{folder_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return file_paths


def main():
  initialize_vertex_ai()
  corpus = create_or_get_corpus() # Uses CORPUS_DISPLAY_NAME & CORPUS_DESCRIPTION

  # Update the .env file with the corpus name
  update_env_file(corpus.name, ENV_FILE_PATH)

  # Upload your local PDF to the corpus

  local_file_path = get_file_paths_in_folder("/Users/jariwm1/Downloads/signia") # Set the correct path
  display_name = "signia" # Set the desired display name
  description = "Signia Stapler Information" # Set the description

  for file_path in local_file_path:
    upload_pdf_to_corpus(
        corpus_name=corpus.name,
        pdf_path=file_path,
        display_name=display_name,
        description=description
    )


  # List all files in the corpus
  list_corpus_files(corpus_name=corpus.name)
  
  # List all files in the corpus
  list_corpus_files(corpus_name=corpus.name)

if __name__ == "__main__":
  main()
