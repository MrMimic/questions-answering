#!/usr/bin/env python3
import logging
import os
import sys
from logging import handlers
from os.path import abspath, dirname, isdir, join
from typing import Optional

import unidecode
import wikipedia
from flask import Flask, make_response, render_template, request
from transformers import AutoModelForQuestionAnswering, AutoTokenizer, pipeline

app = Flask(__name__)

root_path = dirname(abspath(__file__))
models_cache_dir = join(root_path, "models")
logs_dir = join(root_path, "logs")
for folder in [models_cache_dir, logs_dir]:
    if not isdir(folder):
        os.mkdir(folder)

wikipedia.set_lang("fr")

# Get a logger
log_file_path = os.path.join(os.path.dirname(__file__), "logs", "requests.log")
logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# File handler
handler = handlers.RotatingFileHandler(log_file_path, maxBytes=(1048576 * 5), backupCount=7)
handler.setFormatter(formatter)
logger.addHandler(handler)
# Stdout handler
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)


def get_wiki_summary(about: str) -> Optional[str]:
    """ This method allow to search for a page on wikipedia based on a short question.
        Its assumes that the question is short enough to contain mostly stopwords
        and the name of a possible page.
        The most probable page is then loaded and the summary is extracted.

    Args:
        about (str): The short question.

    Returns:
        Optional[str]: The page summary if found.
    """
    # Search for an appropriate top-3 Wikipedia page
    possible_pages = [page for page in wikipedia.search(about, results=3)]
    if len(possible_pages) == 0:
        return None
    # Get pages contained in the question or the most probable from the top-3
    wiki_pages_in_question = [
        page for page in possible_pages if unidecode.unidecode(page.lower()) in unidecode.unidecode(about.lower())
    ]
    if len(wiki_pages_in_question) > 0:
        # If several pages are in the question, we got the longest one
        wiki_page_name = max(wiki_pages_in_question, key=len)
    else:
        wiki_page_name = possible_pages[0]
    # Get summary data, desambiguate if needed
    try:
        page_data = wikipedia.page(wiki_page_name, auto_suggest=False)

    except wikipedia.exceptions.DisambiguationError as e:
        page_data = wikipedia.page(wiki_page_name, auto_suggest=True)
    return page_data.url, page_data.summary


# Create a question answering Huggingface pipeline
qa_tokenizer = AutoTokenizer.from_pretrained(models_cache_dir, local_files_only=True)
qa_model = AutoModelForQuestionAnswering.from_pretrained(models_cache_dir, local_files_only=True)
question_answering = pipeline("question-answering", model=qa_model, tokenizer=qa_tokenizer)


@app.route("/", methods=["GET", "POST"])
def index():
    default_value = "Quand est mort Charlie Chaplin ?"
    question = request.form.get('input',
                                default_value) if request.form.get('input', default_value) != "" else default_value
    logger.info(f"Received question: {question}")
    context = {
        "query": question,
    }

    # Get summary
    try:
        url, summary = get_wiki_summary(about=question)
    except TypeError:
        summary = None

    # Call the pipeline
    if summary is not None:
        pipeline_answer = question_answering(question, summary)
        context["answer"] = pipeline_answer["answer"]
        context["score"] = round(pipeline_answer["score"], 3)
        context["start"] = summary[:pipeline_answer["start"] - 40]
        context["end"] = summary[pipeline_answer["end"] + 40:]
        context["marked"] = summary[pipeline_answer["start"] - 40:pipeline_answer["end"] + 40]
        context["url"] = url
    else:
        context["error"] = "Pas de données trouvées sur Wikipédia."

    headers = {'Content-Type': 'text/html'}
    html_template = make_response(render_template("index.html", **context), 200, headers)
    html_template.mimetype = "text/html"

    return html_template


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
