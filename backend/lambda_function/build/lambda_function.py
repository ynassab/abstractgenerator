import json
import re
import inference_utils
from latex_to_html_map import latex_to_html_map

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
    try:
        # Ensure 'event["body"]' is a JSON string before parsing
        body_content = event['body']
        if isinstance(body_content, dict):
            data = body_content  # already a dictionary, no need to parse
        else:
            data = json.loads(body_content)  # parse the JSON string

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
    # Convert some LaTeX expressions to HTML tags
    html_text = re.sub(r'\$(.*?)\$', r'<i>\1</i>', latex_string)  # Inline math to italics
    html_text = re.sub(r'\^{([^}]+)}', r'<sup>\1</sup>', html_text)  # Superscripts with braces
    html_text = re.sub(r'_{([^}]+)}', r'<sub>\1</sub>', html_text)  # Subscripts with braces
    html_text = re.sub(r'\^([^{}\s]*)\s', r'<sup>\1</sup> ', html_text)  # Superscripts without braces
    html_text = re.sub(r'_([^{}\s]*)\s', r'<sub>\1</sub> ', html_text)  # Subscripts without braces
    html_text = html_text.replace('\n', '<br>')  # Line breaks to <br> tags

    # Remove standalone dollar signs
    html_text = re.sub(r'\$', '', html_text, 1)

    # Convert math symbols to HTML codes
    for latex, html in latex_to_html_map.items():
        html_text = re.sub(latex, html, html_text)

    return html_text

