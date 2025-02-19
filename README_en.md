# UpdateDocs

UpdateDocs aims to automate project documentation using artificial intelligence. With each commit, the [UpdateDocs.py](c:/Users/lucas/Desktop/UpdateDocs/UpdateDocs.py) script updates the project documentation based on changes made to the source code.

---

## About the Script

The [UpdateDocs.py](c:/Users/lucas/Desktop/UpdateDocs/UpdateDocs.py) script performs the following operations:

- **Validation**: Checks the repository directory and verifies the validity of the commit hash.
- **Diff and Edited Files**: Retrieves the list of changed files and the specific diff for each.
- **Mapping Between Code and Documentation**: Generates the path of the documentation files corresponding to the source code files (for example, replacing the `src` folder with `docs` and the `.py` extension with `.md`).
- **Documentation Update**: Reads the current content of the documentation files and uses an LLM (via the LangChain library) to generate Markdown updates.
- **Applying Changes**: Updates the documentation files with the new suggested content.

---

## How to Use?

### 1. Configure Your Post-commit Hook

Follow the steps below to add the script to the Git `post-commit` hook:

1. **Open the terminal.**
2. **Navigate to your Git repository directory:**
    ```sh
    cd /path/to/your/repository
    ```
3. **Create the hooks directory (if it doesn’t exist):**
    ```sh
    mkdir -p .git/hooks
    ```
4. **Edit the `post-commit` file:**
    ```sh
    nano .git/hooks/post-commit
    ```
5. **Add the following content:**
    ```sh
    #!/bin/bash

    # Navigate to the repository root directory
    REPO_DIR=$(git rev-parse --show-toplevel) || exit

    # Capture the latest commit hash
    COMMIT_HASH=$(git rev-parse HEAD)

    # Navigate to the directory where UpdateDocs.py is located
    cd ~/path/to/UpdateDocs || exit

    # Execute the Python script with the repository path and commit hash
    python UpdateDocs.py "$REPO_DIR" "$COMMIT_HASH"
    ```
6. **Save and exit the editor** (in Nano: `Ctrl + O` to save and `Ctrl + X` to exit).
7. **Make the file executable:**
    ```sh
    chmod +x .git/hooks/post-commit
    ```

### 2. Configure Your Gemini API for Free

#### Step 1: Generate the API Key

1. Visit the Gemini site: [Gemini API Documentation](https://ai.google.dev/gemini-api/docs?hl=en).
2. Follow the instructions to create your account and generate an API key.
3. Copy the generated key and store it securely.

#### Step 2: Set Up the Environment Variable

1. **Open the terminal.**
2. **Add the API key as the `GOOGLE_API_KEY` environment variable:**

   **On Linux or macOS:**
   - Edit your configuration file (e.g., `~/.bashrc`):
     ```sh
     nano ~/.bashrc
     ```
   - Add the following line:
     ```sh
     export GOOGLE_API_KEY="your-api-key-here"
     ```
   - Save and close the editor, then run:
     ```sh
     source ~/.bashrc
     ```

   **On Windows:**
   - Open Command Prompt as Administrator and execute:
     ```cmd
     setx GOOGLE_API_KEY "your-api-key-here"
     ```
   - Close and reopen Command Prompt for the changes to take effect.

---

## Folder Structure

For the script to work correctly, the documentation files must follow the same structure as the source code files, changing only the folder and file extension. For example:

```plaintext
my_project/
├── src/
│   ├── Main.java
│   ├── utils/
│   │   └── Helper.py
│   └── components/
│       └── Button.js
└── docs/
    ├── Main.md
    ├── utils/
│   │   └── Helper.md
    └── components/
        └── Button.md
```

**Note:** Ensure that the directory structure and file names are correct so that the documentation file paths are generated properly.

---

## Final Considerations

Once you configure the `post-commit` hook and the API key, the `UpdateDocs.py` file will automatically be triggered with every commit, keeping your project documentation updated based on the changes in the source code.

Feel free to contribute and suggest improvements for this project! 🚀🚀🚀