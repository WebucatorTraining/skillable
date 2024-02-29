# skillable
Skillable Instruction Sets


# Creating instructions for Skillable for Combined Knowledge Courses
## Create the virtual environment.
1. Open the terminal
2. Run `python -m venv .venv`
3. Activate the virtual environment:
   ```
   # Mac:
   source .venv/activate

   # Win:
   .venv\Scripts\activate
   ```
4. Run `pip install -r requirements.txt` to install the required Python libraries.

## Creating the instructions from the epub
1. Combined Knowledge will send an epub file.
2. Rename the epub file with the number of the course (e.g., **55400.epub**) and save it in the **epubs** folder.
3. Run `python create_markdown_from_epub_files.py path_to_epub_file`