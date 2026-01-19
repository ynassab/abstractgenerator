import json
from unittest import mock

from backend.lambda_function.lambda_build import lambda_function

class TestLambdaHandler:
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_context = mock.Mock()
        self.mock_model = mock.Mock()
        self.mock_model.generate_text.return_value = "Generated academic text."

    def test_lambda_handler_wake_up_call(self):
        """Test lambda handler with wake-up call."""
        event = {
            'body': {'wakeUp': True}
        }

        response = lambda_function.lambda_handler(event, self.mock_context)

        assert response['statusCode'] == 200
        assert json.loads(response['body'])['message'] == 'Hello from Lambda!'

    def test_lambda_handler_wake_up_call_json_string_body(self):
        """Test lambda handler with wake-up call when body is JSON string."""
        event = {
            'body': json.dumps({'wakeUp': True})
        }

        response = lambda_function.lambda_handler(event, self.mock_context)

        assert response['statusCode'] == 200
        assert json.loads(response['body'])['message'] == 'Hello from Lambda!'

    @mock.patch('backend.lambda_function.lambda_build.inference_utils.prepare_new_model')
    @mock.patch('backend.lambda_function.lambda_build.lambda_function.latex_to_html')
    def test_lambda_handler_successful_generation(self, mock_latex_to_html, mock_prepare_model):
        """Test successful text generation."""
        mock_prepare_model.return_value = self.mock_model
        mock_latex_to_html.return_value = "<i>Generated academic text.</i>"

        event = {
            'body': {'seed': 'Test seed text'}
        }

        response = lambda_function.lambda_handler(event, self.mock_context)

        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        assert 'output' in response_body
        assert response_body['output'] == "<i>Generated academic text.</i>"

        mock_prepare_model.assert_called_once_with(lambda_function.VOCAB_SIZE)
        self.mock_model.load_weights.assert_called_once_with('model/ckpt_20')
        self.mock_model.generate_text.assert_called_once_with('Test seed text', vocabulary=lambda_function.VOCABULARY)

    @mock.patch('backend.lambda_function.lambda_build.inference_utils.prepare_new_model')
    def test_lambda_handler_text_truncation_at_period(self, mock_prepare_model):
        """Test that generated text is truncated at the last complete sentence."""
        mock_prepare_model.return_value = self.mock_model
        self.mock_model.generate_text.return_value = "First sentence. Second sentence. Incomplete sent"

        event = {
            'body': {'seed': 'Test seed'}}

        with mock.patch('backend.lambda_function.lambda_build.lambda_function.latex_to_html', return_value="processed") as mock_latex:
            response = lambda_function.lambda_handler(event, self.mock_context)

        # Should be called with truncated text ending at last period
        mock_latex.assert_called_once_with("First sentence. Second sentence.")

    @mock.patch('backend.lambda_function.lambda_build.inference_utils.prepare_new_model')
    def test_lambda_handler_no_period_truncation(self, mock_prepare_model):
        """Test behavior when generated text has no periods."""
        mock_prepare_model.return_value = self.mock_model
        self.mock_model.generate_text.return_value = "No periods in this text"

        event = {
            'body': {'seed': 'Test seed'}
        }

        with mock.patch('backend.lambda_function.lambda_build.lambda_function.latex_to_html', return_value="processed") as mock_latex:
            response = lambda_function.lambda_handler(event, self.mock_context)

        # Should be called with original text since no period found
        mock_latex.assert_called_once_with("No periods in this text")

    def test_lambda_handler_json_string_body(self):
        """Test lambda handler when body is a JSON string."""
        event = {
            'body': json.dumps({'seed': 'Test seed text'})
        }

        with mock.patch('backend.lambda_function.lambda_build.inference_utils.prepare_new_model') as mock_prepare:
            mock_prepare.return_value = self.mock_model
            with mock.patch('backend.lambda_function.lambda_build.lambda_function.latex_to_html', return_value="processed"):
                response = lambda_function.lambda_handler(event, self.mock_context)

        assert response['statusCode'] == 200

    def test_lambda_handler_exception_handling(self):
        """Test exception handling in lambda handler."""
        event = {
            'body': {'seed': 'Test seed'}
        }

        with mock.patch('backend.lambda_function.lambda_build.inference_utils.prepare_new_model', side_effect=Exception("Test error")):
            response = lambda_function.lambda_handler(event, self.mock_context)

        assert response['statusCode'] == 500
        response_body = json.loads(response['body'])
        assert 'error' in response_body
        assert response_body['error'] == 'Test error'

    def test_lambda_handler_missing_seed(self):
        """Test lambda handler with missing seed in request."""
        event = {
            'body': {}
        }

        response = lambda_function.lambda_handler(event, self.mock_context)

        assert response['statusCode'] == 500
        response_body = json.loads(response['body'])
        assert 'error' in response_body

    def test_lambda_handler_malformed_json(self):
        """Test lambda handler with malformed JSON in body."""
        event = {
            'body': '{"invalid": json}'
        }

        response = lambda_function.lambda_handler(event, self.mock_context)

        assert response['statusCode'] == 500
        response_body = json.loads(response['body'])
        assert 'error' in response_body


class TestLatexToHtml:
    def test_inline_math_conversion(self):
        """Test conversion of inline math expressions."""
        latex_text = "The equation $E = mc^{2}$ describes mass-energy equivalence."
        expected = "The equation <i>E = mc<sup>2</sup></i> describes mass-energy equivalence."

        result = lambda_function.latex_to_html(latex_text)

        assert result == expected

    def test_superscripts_with_braces(self):
        """Test conversion of superscripts with braces."""
        latex_text = "x^{n+1} is a polynomial."
        expected = "x<sup>n+1</sup> is a polynomial."

        result = lambda_function.latex_to_html(latex_text)

        assert result == expected

    def test_subscripts_with_braces(self):
        """Test conversion of subscripts with braces."""
        latex_text = "H_{2}O is water."
        expected = "H<sub>2</sub>O is water."

        result = lambda_function.latex_to_html(latex_text)

        assert result == expected

    def test_superscripts_without_braces(self):
        """Test conversion of superscripts without braces."""
        latex_text = "x^2 is squared."
        expected = "x<sup>2</sup> is squared."

        result = lambda_function.latex_to_html(latex_text)

        assert result == expected

    def test_subscripts_without_braces(self):
        """Test conversion of subscripts without braces."""
        latex_text = "a_i is indexed."
        expected = "a<sub>i</sub> is indexed."

        result = lambda_function.latex_to_html(latex_text)

        assert result == expected

    def test_line_breaks_conversion(self):
        """Test conversion of line breaks."""
        latex_text = r"First line.\nSecond line."
        expected = "First line.<br>Second line."

        result = lambda_function.latex_to_html(latex_text)

        assert result == expected

    def test_standalone_dollar_removal(self):
        """Test removal of standalone dollar signs."""
        latex_text = "This has a standalone $ sign."
        expected = "This has a standalone  sign."

        result = lambda_function.latex_to_html(latex_text)

        # Should remove one standalone dollar sign
        assert '$' not in result or result.count('$') < latex_text.count('$')

    def test_greek_letters_conversion(self):
        """Test conversion of Greek letters."""
        latex_text = "\\alpha and \\beta are Greek letters."
        expected = "&alpha; and &beta; are Greek letters."

        result = lambda_function.latex_to_html(latex_text)

        assert result == expected

    def test_math_symbols_conversion(self):
        """Test conversion of mathematical symbols."""
        latex_text = "\\infty represents infinity."
        expected = "&infin; represents infinity."

        result = lambda_function.latex_to_html(latex_text)

        assert result == expected

    def test_complex_expression(self):
        """Test conversion of complex LaTeX expression."""
        latex_text = "$\\alpha^{2} + \\beta_{max}$ represents the formula\\nfor the calculation."

        result = lambda_function.latex_to_html(latex_text)

        # Should convert math mode, superscripts, subscripts, Greek letters, and line breaks
        assert "<i>" in result and "</i>" in result  # Math mode
        assert "<sup>" in result and "</sup>" in result  # Superscripts
        assert "<sub>" in result and "</sub>" in result  # Subscripts
        assert "&alpha;" in result and "&beta;" in result  # Greek letters
        assert "<br>" in result  # Line breaks

    def test_multiple_inline_math(self):
        """Test multiple inline math expressions."""
        latex_text = "First $x^{2}$ and second $y^{3}$ equations."

        result = lambda_function.latex_to_html(latex_text)

        # Should have two italic sections
        assert result.count("<i>") == 2
        assert result.count("</i>") == 2
        assert "<sup>2</sup>" in result
        assert "<sup>3</sup>" in result

    def test_nested_expressions(self):
        """Test nested superscript and subscript expressions."""
        latex_text = "x^{a_i} represents nested notation."

        result = lambda_function.latex_to_html(latex_text)

        assert "<sup>" in result and "</sup>" in result
        assert "<sub>" in result and "</sub>" in result

    def test_empty_string(self):
        """Test conversion of empty string."""
        result = lambda_function.latex_to_html("")
        assert result == ""

    def test_no_latex_content(self):
        """Test text with no LaTeX content."""
        latex_text = "This is plain text with no special formatting."

        result = lambda_function.latex_to_html(latex_text)

        assert result == latex_text

    def test_arrow_symbols(self):
        """Test conversion of arrow symbols."""
        latex_text = "\\rightarrow shows direction."
        expected = "&rarr; shows direction."

        result = lambda_function.latex_to_html(latex_text)

        assert result == expected

    def test_mathematical_operators(self):
        """Test conversion of mathematical operators."""
        latex_text = "a \\times b \\neq c"
        expected = "a &times; b &ne; c"

        result = lambda_function.latex_to_html(latex_text)

        assert result == expected


class TestConstants:
    def test_vocabulary_exists(self):
        """Test that VOCABULARY constant exists and is a list."""
        assert hasattr(lambda_function, 'VOCABULARY')
        assert isinstance(lambda_function.VOCABULARY, list)
        assert len(lambda_function.VOCABULARY) > 0

    def test_vocab_size_matches_vocabulary(self):
        """Test that VOCAB_SIZE matches length of VOCABULARY."""
        assert hasattr(lambda_function, 'VOCAB_SIZE')
        assert lambda_function.VOCAB_SIZE == len(lambda_function.VOCABULARY)

    def test_vocabulary_contains_expected_characters(self):
        """Test that vocabulary contains expected character types."""
        vocab = lambda_function.VOCABULARY

        # Should contain basic ASCII characters
        assert ' ' in vocab  # space
        assert 'a' in vocab  # lowercase letter
        assert 'A' in vocab  # uppercase letter
        assert '0' in vocab  # digit
        assert '.' in vocab  # punctuation
        assert '[UNK]' in vocab  # unknown token

    def test_vocabulary_unk_token_first(self):
        """Test that [UNK] token is first in vocabulary."""
        assert lambda_function.VOCABULARY[0] == '[UNK]'

    def test_vocabulary_size_expected_value(self):
        """Test that vocabulary has expected size."""
        # Based on the provided VOCABULARY constant
        assert lambda_function.VOCAB_SIZE == 109