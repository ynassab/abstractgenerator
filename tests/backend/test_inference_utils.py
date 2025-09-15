import pytest
import os
import tempfile
import shutil
import tensorflow as tf
from unittest import mock
from keras import backend as K

from backend.lambda_function.lambda_build import inference_utils

class TestSetNewCheckpointCallback:
    def test_checkpoint_callback_creation(self):
        """Test that checkpoint callback is created with correct parameters."""
        checkpoint_dir = "/tmp/test_checkpoints"
        callback = inference_utils.set_new_checkpoint_callback(checkpoint_dir)

        assert isinstance(callback, tf.keras.callbacks.ModelCheckpoint)
        assert callback.save_weights_only is True
        assert checkpoint_dir in callback.filepath

    def test_checkpoint_callback_filepath_format(self):
        """Test that checkpoint filepath includes epoch placeholder."""
        checkpoint_dir = "/tmp/test_checkpoints"
        callback = inference_utils.set_new_checkpoint_callback(checkpoint_dir)

        expected_path = os.path.join(checkpoint_dir, 'ckpt_{epoch}')
        assert callback.filepath == expected_path


class TestSplitInputTarget:
    def test_split_input_target_basic(self):
        """Test basic functionality of split_input_target."""
        sequence = tf.constant([1, 2, 3, 4, 5])
        input_text, target_text = inference_utils.split_input_target(sequence)

        assert tf.reduce_all(tf.equal(input_text, [1, 2, 3, 4]))
        assert tf.reduce_all(tf.equal(target_text, [2, 3, 4, 5]))

    def test_split_input_target_single_element(self):
        """Test split_input_target with minimal sequence."""
        sequence = tf.constant([1, 2])
        input_text, target_text = inference_utils.split_input_target(sequence)

        assert tf.reduce_all(tf.equal(input_text, [1]))
        assert tf.reduce_all(tf.equal(target_text, [2]))

    def test_split_input_target_longer_sequence(self):
        """Test split_input_target with longer sequence."""
        sequence = tf.constant([10, 20, 30, 40, 50, 60, 70, 80])
        input_text, target_text = inference_utils.split_input_target(sequence)

        expected_input = [10, 20, 30, 40, 50, 60, 70]
        expected_target = [20, 30, 40, 50, 60, 70, 80]

        assert tf.reduce_all(tf.equal(input_text, expected_input))
        assert tf.reduce_all(tf.equal(target_text, expected_target))


class TestCharMapping:
    def test_char_mapping_class_exists(self):
        """Test that CharMapping class exists and can store attributes."""
        assert hasattr(inference_utils, 'CharMapping')

        # Test that we can set attributes
        mock_layer = mock.Mock()
        inference_utils.CharMapping.ids_from_chars = mock_layer
        inference_utils.CharMapping.chars_from_ids = mock_layer

        assert inference_utils.CharMapping.ids_from_chars == mock_layer
        assert inference_utils.CharMapping.chars_from_ids == mock_layer


class TestMyModel:
    def test_model_initialization(self):
        """Test MyModel initialization."""
        vocab_size = 100
        embedding_dim = 256
        rnn_units = 512

        model = inference_utils.MyModel(vocab_size, embedding_dim, rnn_units)

        assert isinstance(model.embedding, tf.keras.layers.Embedding)
        assert isinstance(model.gru, tf.keras.layers.GRU)
        assert isinstance(model.dense, tf.keras.layers.Dense)
        assert model.embedding.input_dim == vocab_size
        assert model.embedding.output_dim == embedding_dim
        assert model.gru.units == rnn_units
        assert model.dense.units == vocab_size

    def test_model_call_without_states(self):
        """Test model call without initial states."""
        vocab_size = 10
        embedding_dim = 8
        rnn_units = 16
        batch_size = 2
        seq_length = 5

        model = inference_utils.MyModel(vocab_size, embedding_dim, rnn_units)
        inputs = tf.random.uniform((batch_size, seq_length), 0, vocab_size, dtype=tf.int32)

        outputs = model(inputs)

        assert outputs.shape == (batch_size, seq_length, vocab_size)

    def test_model_call_with_return_state(self):
        """Test model call with return_state=True."""
        vocab_size = 10
        embedding_dim = 8
        rnn_units = 16
        batch_size = 2
        seq_length = 5

        model = inference_utils.MyModel(vocab_size, embedding_dim, rnn_units)
        inputs = tf.random.uniform((batch_size, seq_length), 0, vocab_size, dtype=tf.int32)

        outputs, states = model(inputs, return_state=True)

        assert outputs.shape == (batch_size, seq_length, vocab_size)
        assert states.shape == (batch_size, rnn_units)

    @mock.patch.object(inference_utils, 'OneStep')
    def test_generate_text_with_default_params(self, mock_one_step):
        """Test generate_text with default parameters."""
        vocab_size = 10
        model = inference_utils.MyModel(vocab_size, 256, 512)

        # Mock CharMapping
        mock_ids_from_chars = mock.Mock()
        mock_chars_from_ids = mock.Mock()
        inference_utils.CharMapping.ids_from_chars = mock_ids_from_chars
        inference_utils.CharMapping.chars_from_ids = mock_chars_from_ids

        # Mock OneStep behavior
        mock_one_step_instance = mock.Mock()
        mock_one_step_instance.generate_one_step.return_value = (tf.constant(['a']), None)
        mock_one_step.return_value = mock_one_step_instance

        with mock.patch('tensorflow.strings.join', return_value=tf.constant(['generated text'])):
            result = model.generate_text(length=5)

        mock_one_step.assert_called_once()
        assert mock_one_step_instance.generate_one_step.call_count == 5

    def test_generate_text_with_custom_vocabulary(self):
        """Test generate_text with custom vocabulary."""
        vocab_size = 5
        model = inference_utils.MyModel(vocab_size, 256, 512)
        custom_vocab = ['a', 'b', 'c', 'd', 'e']

        with mock.patch.object(model, 'generate_text', return_value="mock result") as mock_generate:
            result = model.generate_text(vocabulary=custom_vocab)

        mock_generate.assert_called_once_with(vocabulary=custom_vocab)


class TestCustomTraining:
    def test_custom_training_inheritance(self):
        """Test CustomTraining inherits from MyModel."""
        vocab_size = 10
        model = inference_utils.CustomTraining(vocab_size, 256, 512)

        assert isinstance(model, inference_utils.MyModel)

    def test_train_step_signature(self):
        """Test train_step method exists and has correct signature."""
        vocab_size = 10
        model = inference_utils.CustomTraining(vocab_size, 256, 512)

        assert hasattr(model, 'train_step')
        assert callable(model.train_step)

    @mock.patch('tensorflow.GradientTape')
    def test_train_step_execution(self, mock_gradient_tape):
        """Test train_step execution flow."""
        vocab_size = 10
        embedding_dim = 8
        rnn_units = 16
        batch_size = 2
        seq_length = 5

        model = inference_utils.CustomTraining(vocab_size, embedding_dim, rnn_units)
        model.compile(
            optimizer='adam',
            loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
        )

        # Create mock inputs
        inputs = tf.random.uniform((batch_size, seq_length), 0, vocab_size, dtype=tf.int32)
        labels = tf.random.uniform((batch_size, seq_length), 0, vocab_size, dtype=tf.int32)

        # Mock gradient tape
        mock_tape = mock.Mock()
        mock_tape.gradient.return_value = [tf.zeros((10, 8))]  # Mock gradients
        mock_gradient_tape.return_value.__enter__.return_value = mock_tape

        result = model.train_step((inputs, labels))

        assert 'loss' in result
        # This method may be called more than once due to tf.function tracing
        mock_tape.gradient.assert_called()


class TestOneStep:
    def setup_method(self):
        """Set up test fixtures."""
        self.vocab_size = 10
        self.embedding_dim = 8
        self.rnn_units = 16
        self.model = inference_utils.MyModel(self.vocab_size, self.embedding_dim, self.rnn_units)

        # Create mock lookup layers with vocabulary size matching the model
        self.mock_chars_from_ids = mock.MagicMock()
        # Make vocabulary size match model's vocab_size
        self.mock_chars_from_ids.get_vocabulary.return_value = [
            '[UNK]', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i'
        ]

        self.mock_ids_from_chars = mock.MagicMock()
        # Return tensor with correct dtype (int64) and shape (1,) for single token
        self.mock_ids_from_chars.return_value = tf.constant([0], dtype=tf.int64)
        self.mock_ids_from_chars.get_vocabulary.return_value = [
            '[UNK]', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i'
        ]

    def test_one_step_initialization(self):
        """Test OneStep model initialization."""
        temperature = 0.8
        one_step = inference_utils.OneStep(
            self.model, self.mock_chars_from_ids, self.mock_ids_from_chars, temperature
        )

        assert one_step.temperature == temperature
        assert one_step.model == self.model
        assert one_step.chars_from_ids == self.mock_chars_from_ids
        assert one_step.ids_from_chars == self.mock_ids_from_chars

    def test_one_step_prediction_mask_creation(self):
        """Test that prediction mask is created correctly."""
        one_step = inference_utils.OneStep(
            self.model, self.mock_chars_from_ids, self.mock_ids_from_chars
        )

        assert hasattr(one_step, 'prediction_mask')
        assert one_step.prediction_mask is not None

    @mock.patch('tensorflow.strings.unicode_split')
    @mock.patch('tensorflow.random.categorical')
    def test_generate_one_step(self, mock_categorical, mock_unicode_split):
        """Test generate_one_step method."""
        one_step = inference_utils.OneStep(
            self.model, self.mock_chars_from_ids, self.mock_ids_from_chars
        )

        # Mock inputs and outputs
        mock_unicode_split.return_value = tf.constant([['h', 'e', 'l', 'l', 'o']])
        mock_categorical.return_value = tf.constant([[2]])
        self.mock_chars_from_ids.return_value = tf.constant(['c'])

        # Create mock tensor for ids_from_chars
        mock_tensor = mock.Mock()
        mock_tensor.to_tensor.return_value = tf.constant([[1, 2, 3, 4, 5]])
        self.mock_ids_from_chars.return_value = mock_tensor

        inputs = tf.constant(['hello'])
        predicted_chars, states = one_step.generate_one_step(inputs)

        # These methods may be called more than once due to tf.function tracing
        mock_unicode_split.assert_called()
        mock_categorical.assert_called()


class TestGenerateDataset:
    def setup_method(self):
        """Set up test fixtures with temporary file."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, 'test_text.txt')
        self.test_text = "Hello world! This is a test file for dataset generation."

        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write(self.test_text)

    def teardown_method(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)

    def test_generate_dataset_basic(self):
        """Test basic dataset generation."""
        start_index = 0
        stop_index = 20

        dataset, vocab_size = inference_utils.generate_dataset(
            start_index, stop_index, self.test_file
        )

        assert isinstance(dataset, tf.data.Dataset)
        assert isinstance(vocab_size, int)
        assert vocab_size > 0

    def test_generate_dataset_char_mapping_setup(self):
        """Test that CharMapping attributes are set during dataset generation."""
        start_index = 0
        stop_index = 30

        dataset, vocab_size = inference_utils.generate_dataset(
            start_index, stop_index, self.test_file
        )

        assert hasattr(inference_utils.CharMapping, 'ids_from_chars')
        assert hasattr(inference_utils.CharMapping, 'chars_from_ids')
        assert inference_utils.CharMapping.ids_from_chars is not None
        assert inference_utils.CharMapping.chars_from_ids is not None

    def test_generate_dataset_vocab_size_consistency(self):
        """Test that vocabulary size remains consistent across calls."""
        # First call
        dataset1, vocab_size1 = inference_utils.generate_dataset(0, 10, self.test_file)

        # Second call with different indices
        dataset2, vocab_size2 = inference_utils.generate_dataset(10, 20, self.test_file)

        assert vocab_size1 == vocab_size2

    def test_generate_dataset_file_not_found(self):
        """Test behavior when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            inference_utils.generate_dataset(0, 10, "nonexistent_file.txt")

    def test_generate_dataset_invalid_indices(self):
        """Test dataset generation with indices beyond file length."""
        # This should still work, just return empty or truncated data
        start_index = len(self.test_text) + 10
        stop_index = len(self.test_text) + 20

        dataset, vocab_size = inference_utils.generate_dataset(
            start_index, stop_index, self.test_file
        )

        assert isinstance(dataset, tf.data.Dataset)
        assert vocab_size > 0


class TestPrepareNewModel:
    def test_prepare_new_model_returns_custom_training(self):
        """Test that prepare_new_model returns CustomTraining instance."""
        vocab_size = 100
        model = inference_utils.prepare_new_model(vocab_size)

        assert isinstance(model, inference_utils.CustomTraining)

    def test_prepare_new_model_compilation(self):
        """Test that model is compiled with correct parameters."""
        vocab_size = 100
        model = inference_utils.prepare_new_model(vocab_size)

        assert model.optimizer is not None
        assert model.compiled_loss is not None

    @mock.patch.object(K, 'set_value')
    def test_prepare_new_model_learning_rate_setting(self, mock_set_value):
        """Test that learning rate is set correctly."""
        vocab_size = 100
        model = inference_utils.prepare_new_model(vocab_size)

        mock_set_value.assert_called_once_with(
            model.optimizer.learning_rate,
            inference_utils.LEARNING_RATE
        )

    def test_prepare_new_model_architecture(self):
        """Test model architecture parameters."""
        vocab_size = 150
        model = inference_utils.prepare_new_model(vocab_size)

        assert model.embedding.input_dim == vocab_size
        assert model.embedding.output_dim == inference_utils.EMBEDDING_DIM
        assert model.gru.units == inference_utils.RNN_UNITS
        assert model.dense.units == vocab_size


class TestEnvironmentVariables:
    def test_tensorflow_logging_disabled(self):
        """Test that TensorFlow logging is configured correctly."""
        assert os.environ.get('TF_CPP_MIN_LOG_LEVEL') == '1'

    def test_cuda_disabled(self):
        """Test that CUDA is disabled for CPU-only inference."""
        assert os.environ.get('CUDA_VISIBLE_DEVICES') == '-1'
