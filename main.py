#!/usr/bin/env python3
import os
from os.path import abspath, dirname, isdir, join
from typing import Optional

import unidecode
import wikipedia
from flask import Flask, render_template, request
from transformers import AutoModelForQuestionAnswering, AutoTokenizer, pipeline

app = Flask(__name__)
models_cache_dir = join(dirname(abspath(__file__)), "models")
if not isdir(models_cache_dir):
    os.mkdir(models_cache_dir)
wikipedia.set_lang("fr")


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
        page_data = wikipedia.page(wiki_page_name, auto_suggest=False).summary
    except wikipedia.exceptions.DisambiguationError as e:
        page_data = wikipedia.page(wiki_page_name, auto_suggest=True).summary
    return page_data


# Create a question answering Huggingface pipeline
qa_tokenizer = AutoTokenizer.from_pretrained("etalab-ia/camembert-base-squadFR-fquad-piaf", cache_dir=models_cache_dir)
qa_model = AutoModelForQuestionAnswering.from_pretrained("etalab-ia/camembert-base-squadFR-fquad-piaf",
                                                         cache_dir=models_cache_dir)
question_answering = pipeline("question-answering", model=qa_model, tokenizer=qa_tokenizer)


@app.route("/", methods=["GET", "POST"])
def index():
    context = {}
    default_value = "Quand est mort Charlie Chaplin ?"
    question = request.form.get('input',
                                default_value) if request.form.get('input', default_value) != "" else default_value
    context["query"] = question

    # Get summary
    summary = get_wiki_summary(about=question)

    # Call the pipeline
    if summary is not None:
        answer = question_answering(question, summary)
        start = summary[:answer['start']]
        end = summary[answer['end']:]
        marked = summary[answer['start']:answer['end']]
    else:
        answer = None

    context["start"] = start
    context["end"] = end
    context["marked"] = marked
    context["answer"] = answer

    html_template = render_template("index.html", **context)

    return html_template


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
