"""
Abstract Generator Backend

Serves as the backend API for the Abstract Generator web application. Generates academic-style
text based on user input. The underlying model was trained on academic article abstracts and
generates text that mimics the style and structure of scholarly writing.

@author Yahia Nassab
"""

import json
import re
from . import inference_utils
from .latex_to_html_map import latex_to_html_map

# Character vocabulary used during model training
VOCABULARY = ['[UNK]', ' ', '!', '"', '#', '$', '%', '&', "'",
              '(', ')', '*', '+', ',', '-', '.', '/', '0', '1',
              '2', '3', '4', '5', '6', '7', '8', '9', ':', ';',
              '<', '=', '>', '?', '@', 'A', 'B', 'C', 'D', 'E',
              'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O',
              'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y',
              'Z', '[', '\\', ']', '^', '_', '`', 'a', 'b', 'c',
              'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
              'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w',
              'x', 'y', 'z', '{', '|', '}', '~', '\x7f', '\x80',
              '\x88', '\x89', '\x93', '\x94', '\x99', '\x9c', '\x9d',
              '\x9e', '¤', '¿', 'â']
VOCAB_SIZE = len(VOCABULARY)


def lambda_handler(event, context):
    """
    AWS Lambda entry point for academic text generation API.

    This function serves as the main handler for HTTP requests to generate academic-style
    text using a pre-trained character-level RNN model. It processes the input seed text,
    loads the trained model, generates new text, and returns HTML-formatted output.

    Args:
        event (dict): AWS Lambda event object containing the HTTP request data.
                      Expected structure (for Lambda warm-up calls):
                      {
                         "body": {
                             "wakeUp": true
                         }
                      }
                      Expected structure (for all usage within 15 minutes after a Lambda warm-up call):
                      {
                         "body": {
                             "seed": "initial text to start generation",
                         }
                      }
        context (LambdaContext): AWS Lambda context object containing runtime information.
                                 Not used in this implementation but required by Lambda.

    Returns:
        dict: HTTP response object with the following structure:
              Success (200):
              {
                  "statusCode": 200,
                  "body": "{\"output\": \"<HTML-formatted generated text>\"}"
              }

              Warm-up response (200):
              {
                  "statusCode": 200,
                  "body": "\"Hello from Lambda!\""
              }

              Error (500):
              {
                  "statusCode": 500,
                  "body": "{\"error\": \"<error description>\"}"
              }
    """
    try:
        # Ensure 'event["body"]' is a JSON string before parsing
        body_content = event['body']
        if isinstance(body_content, dict):
            data = body_content
        else:
            data = json.loads(body_content)

        # Return blank response if request is a wake-up call
        if 'wakeUp' in data:
            return {
                'statusCode': 200,
                'body': json.dumps('Hello from Lambda!'),
            }

        seed = data['seed']

        model = inference_utils.prepare_new_model(VOCAB_SIZE)
        model.load_weights(f'model/ckpt_20')
        response = model.generate_text(seed, vocabulary=VOCABULARY)

        # Truncate the result to the last complete sentence
        last_period_index = response.rfind('.')
        if last_period_index != -1:
            response = response[:last_period_index+1]

        return {
            'statusCode': 200,
            'body': json.dumps({"output": latex_to_html(response)}),
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
        }


def latex_to_html(latex_string):
    """
    Convert LaTeX mathematical expressions and symbols to HTML format suitable for
    web display.

    Args:
        latex_string (str): Input text containing LaTeX expressions and symbols.
                            Examples: "$\\alpha^2$", "H_2O", "\\beta_{max}"

    Returns:
        str: HTML-formatted string with LaTeX expressions converted to HTML markup.
             Mathematical expressions are converted to italics, superscripts use <sup>,
             subscripts use <sub>, and special symbols are converted to HTML entities.

    Conversion Rules:
        - $...$ : Inline math expressions → <i>...</i> (italics)
        - ^{...} : Superscripts with braces → <sup>...</sup>
        - _{...} : Subscripts with braces → <sub>...</sub>
        - ^text : Superscripts without braces → <sup>text</sup>
        - _text : Subscripts without braces → <sub>text</sub>
        - \\n : Line breaks → <br> tags
        - Greek letters and symbols → HTML entities (via latex_to_html_map)

    Examples:
        Input: "The equation $E = mc^2$ shows energy-mass equivalence."
        Output: "The equation <i>E = mc<sup>2</sup></i> shows energy-mass equivalence."

        Input: "Water molecule H_2O contains \\alpha particles."
        Output: "Water molecule H<sub>2</sub>O contains &alpha; particles."

        Input: "The function f(x) = x^{n+1} represents polynomial growth."
        Output: "The function f(x) = x<sup>n+1</sup> represents polynomial growth."
    """
    html_text = re.sub(r'\$(.*?)\$', r'<i>\1</i>', latex_string)  # Inline math to italics
    html_text = re.sub(r'\^{([^}]+)}', r'<sup>\1</sup>', html_text)  # Superscripts with braces
    html_text = re.sub(r'_{([^}]+)}', r'<sub>\1</sub>', html_text)  # Subscripts with braces
    html_text = re.sub(r'\^([^{}\s]*)\s', r'<sup>\1</sup> ', html_text)  # Superscripts without braces
    html_text = re.sub(r'_([^{}\s]*)\s', r'<sub>\1</sub> ', html_text)  # Subscripts without braces

    # Remove standalone dollar signs
    html_text = re.sub(r'\$', '', html_text, 1)

    # Convert math symbols to HTML codes
    for latex, html in latex_to_html_map.items():
        html_text = re.sub(latex, html, html_text)

    # Replace newlines with <br> tags
    html_text = html_text.replace(r'\n', '<br>')
    html_text = html_text.replace('\\newline', '<br>')  # LaTeX format
    html_text = html_text.replace(r'\\', '<br>')  # Alternative LaTeX format; must be performed last

    return html_text

