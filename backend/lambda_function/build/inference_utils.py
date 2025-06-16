import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'  # Turn off info messages
# Note that in *training*, GPU is used, but in an *inference* context in
# the AWS Lambda function, only CPU is used
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Use CPU only; don't look for GPU
import tensorflow as tf
from keras import backend as K

BATCH_SIZE = 16
BUFFER_SIZE = 10000
EPOCHS = 20
EMBEDDING_DIM = 256
RNN_UNITS = 1024
LEARNING_RATE = 0.0001
SEQ_LENGTH = 500

def set_new_checkpoint_callback(checkpoint_dir):
    """
    Creates a ModelCheckpoint callback for saving model weights during training.

    Args:
        checkpoint_dir (str): Directory path where checkpoints will be saved.
                              Each checkpoint will be saved as 'ckpt_{epoch}' where
                              epoch is automatically set during training.

    Returns:
        tf.keras.callbacks.ModelCheckpoint: Configured checkpoint callback that saves
                                            weights only at the end of each epoch.
    """
    # The {epoch} placeholder is automatically formatted by ModelCheckpoint
    # when the callback is used in model.fit(). The fit() method passes the
    # current epoch number to the callback, which substitutes it into the filename.
    checkpoint_prefix = os.path.join(checkpoint_dir, 'ckpt_{epoch}')
    checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
                filepath=checkpoint_prefix,
                save_weights_only=True)
    return checkpoint_callback


def split_input_target(sequence):
    """
    Splits a sequence into input and target sequences for next-character prediction.

    Args:
        sequence (tf.Tensor): Input sequence of character IDs with shape [seq_length + 1].

    Returns:
        tuple: A tuple containing:
            - input_text (tf.Tensor): Input sequence [:-1] for training
            - target_text (tf.Tensor): Target sequence [1:] for prediction

    Example:
        If sequence = [1, 2, 3, 4, 5], then:
        input_text = [1, 2, 3, 4]
        target_text = [2, 3, 4, 5]
    """
    input_text = sequence[:-1]
    target_text = sequence[1:]
    return input_text, target_text


class CharMapping():
    """
    Static container class for character-to-ID mapping layers.

    This class serves as a namespace to store the StringLookup layers
    that convert between characters and integer IDs. The mapping layers
    are set as class attributes during dataset generation.

    Attributes:
        ids_from_chars (tf.keras.layers.StringLookup): Maps characters to integer IDs
        chars_from_ids (tf.keras.layers.StringLookup): Maps integer IDs to characters
    """
    pass


class MyModel(tf.keras.Model):
    """
    Character-level text generation model using GRU architecture.

    This model implements a sequence-to-sequence architecture with:
    - Embedding layer for character representations
    - GRU layer for sequence modeling
    - Dense layer for character prediction

    Args:
        vocab_size (int): Size of the character vocabulary
        embedding_dim (int): Dimension of character embeddings
        rnn_units (int): Number of units in the GRU layer
    """

    def __init__(self, vocab_size, embedding_dim, rnn_units):
        """Initialize the model layers."""
        super().__init__(self)
        self.embedding = tf.keras.layers.Embedding(vocab_size, embedding_dim)
        self.gru = tf.keras.layers.GRU(rnn_units,
                                        return_sequences=True,
                                        return_state=True)
        self.dense = tf.keras.layers.Dense(vocab_size)

    def call(self, inputs, states=None, return_state=False, training=False):
        """
        Forward pass through the model.

        Args:
            inputs (tf.Tensor): Input sequence of character IDs
            states (tf.Tensor, optional): Initial GRU states. Defaults to None.
            return_state (bool): Whether to return the final GRU states. Defaults to False.
            training (bool): Whether the model is in training mode. Defaults to False.

        Returns:
            tf.Tensor or tuple: Model predictions (logits over vocabulary).
                                If return_state=True, returns (predictions, states).
        """
        x = inputs
        x = self.embedding(x, training=training)
        if states is None:
            states = self.gru.get_initial_state(x)
        x, states = self.gru(x, initial_state=states, training=training)
        x = self.dense(x, training=training)

        if return_state:
            return x, states
        else:
            return x

    def generate_text(self, seed='Herein, we describe a new model for', length=1000, vocabulary=None):
        """
        Generate text using the trained model.

        Args:
            seed (str): Initial text to start generation. Defaults to 'Herein, we describe a new model for'.
            length (int): Number of characters to generate. Defaults to 1000.
            vocabulary (list, optional): Custom vocabulary list. If None, uses CharMapping. Defaults to None.

        Returns:
            str: Generated text string starting with the seed text.
        """
        if vocabulary is None:
            ids_from_chars = CharMapping.ids_from_chars
            chars_from_ids = CharMapping.chars_from_ids
        else:
            ids_from_chars = tf.keras.layers.StringLookup(
                                vocabulary=vocabulary, mask_token=None)
            chars_from_ids = tf.keras.layers.StringLookup(
                                vocabulary=vocabulary, invert=True, mask_token=None)

        one_step_model = OneStep(self, chars_from_ids, ids_from_chars)
        states = None
        next_char = tf.constant([seed])
        result = [next_char]

        for _ in range(length):
            next_char, states = one_step_model.generate_one_step(next_char, states=states)
            result.append(next_char)

        result = tf.strings.join(result)
        response = result[0].numpy().decode('utf-8')
        return response


class CustomTraining(MyModel):
    """
    Custom training wrapper for MyModel with custom training step implementation.

    This class extends MyModel to provide a custom training step that manually
    computes gradients and applies optimizer updates. Inherits all functionality
    from MyModel while allowing for custom training behavior.
    """

    @tf.function
    def train_step(self, inputs):
        """
        Custom training step implementation.

        Args:
            inputs (tuple): Tuple containing (input_batch, target_batch)

        Returns:
            dict: Dictionary containing the computed loss value

        Note:
            This method manually computes gradients using GradientTape
            and applies them using the optimizer, providing more control
            over the training process than the default Keras training loop.
        """
        inputs, labels = inputs
        with tf.GradientTape() as tape:
            predictions = self(inputs, training=True)
            loss = self.loss(labels, predictions)
        grads = tape.gradient(loss, self.trainable_variables)
        self.optimizer.apply_gradients(zip(grads, self.trainable_variables))
        return {'loss': loss}


class OneStep(tf.keras.Model):
    """
    Single-step text generation model for efficient inference.

    This model wraps a trained text generation model to enable efficient
    character-by-character generation. It handles character tokenization,
    prediction masking, and temperature-based sampling.

    Args:
        model (MyModel): Trained text generation model
        chars_from_ids (tf.keras.layers.StringLookup): Layer to convert IDs to characters
        ids_from_chars (tf.keras.layers.StringLookup): Layer to convert characters to IDs
        temperature (float): Temperature parameter for sampling. Defaults to 1.0.
    """

    def __init__(self, model, chars_from_ids, ids_from_chars, temperature=1.0):
        """Initialize the one-step generation model."""
        super().__init__()
        self.temperature = temperature
        self.model = model
        self.chars_from_ids = chars_from_ids
        self.ids_from_chars = ids_from_chars

        # Create a mask to prevent "[UNK]" from being generated.
        skip_ids = self.ids_from_chars(['[UNK]'])[:, None]
        sparse_mask = tf.SparseTensor(
            # Put a -inf at each bad index.
            values=[-float('inf')]*len(skip_ids),
                    indices=skip_ids,
                    # Match the shape to the vocabulary
                    dense_shape=[len(ids_from_chars.get_vocabulary())])
        self.prediction_mask = tf.sparse.to_dense(sparse_mask)

    @tf.function
    def generate_one_step(self, inputs, states=None):
        """
        Generate one character given input text and current model states.

        Args:
            inputs (tf.Tensor): Input text as string tensor
            states (tf.Tensor, optional): Current GRU states. Defaults to None.

        Returns:
            tuple: A tuple containing:
                   - predicted_chars (tf.Tensor): Next predicted character
                   - states (tf.Tensor): Updated model states

        Note:
            This method performs the following steps:
            1. Convert input strings to character IDs
            2. Run the model to get predictions
            3. Apply temperature scaling and prediction masking
            4. Sample the next character using categorical sampling
            5. Convert back to character representation
        """
        # Convert strings to token IDs.
        input_chars = tf.strings.unicode_split(inputs, 'UTF-8')
        input_ids = self.ids_from_chars(input_chars).to_tensor()

        # Run the model (predicted_logits.shape is [batch, char, next_char_logits])
        predicted_logits, states = self.model(inputs=input_ids, states=states,
                                              return_state=True)
        # Only use the last prediction
        predicted_logits = predicted_logits[:, -1, :]
        predicted_logits = predicted_logits/self.temperature

        # Apply the prediction mask to prevent "[UNK]" from being generated
        predicted_logits = predicted_logits + self.prediction_mask

        # Sample the output logits to generate token IDs
        predicted_ids = tf.random.categorical(predicted_logits, num_samples=1)
        predicted_ids = tf.squeeze(predicted_ids, axis=-1)

        # Convert from token ids to characters
        predicted_chars = self.chars_from_ids(predicted_ids)

        # Return the characters and model state
        return predicted_chars, states


def generate_dataset(start_index, stop_index, path_to_file='abstracts.txt'):
    """
    Generate a TensorFlow dataset from a subset of a text file for incremental training.

    This function creates manageable training batches by subdividing the total dataset
    into smaller chunks that fit within hardware memory constraints. It loads only
    a specified portion of the text file (e.g., 100M characters) for each training
    iteration, enabling progressive training through the entire dataset.

    Args:
        start_index (int): Starting character index in the text file for this batch
        stop_index (int): Ending character index in the text file for this batch
        path_to_file (str): Path to the text file. Defaults to 'abstracts.txt'.

    Returns:
        tuple: A tuple containing:
               - dataset (tf.data.Dataset): Preprocessed dataset with input/target pairs
               - vocab_size (int): Size of the character vocabulary (constant across batches)

    Note:
        This function enables incremental training by:
        1. Loading only a subset of the full text file (start_index:stop_index)
        2. Creating character vocabulary from the ENTIRE file (for consistency)
        3. Converting the text subset to character ID sequences
        4. Creating overlapping sequences of length SEQ_LENGTH+1
        5. Splitting sequences into input/target pairs
        6. Shuffling, batching, and prefetching the dataset

        The vocabulary is built from the complete file to ensure consistent
        character mappings across all training batches. The CharMapping class
        attributes are set as side effects and remain constant (vocab_size=109).

        Example usage for incremental training:
        - Batch 1: characters 0 to 100M
        - Batch 2: characters 100M to 200M
        - Batch 3: characters 200M to 300M, etc.
    """
    text = open(path_to_file, 'r', encoding='utf-8').read()
    vocab = sorted(set(text))

    CharMapping.ids_from_chars = tf.keras.layers.StringLookup(
            vocabulary=list(vocab), mask_token=None)
    CharMapping.chars_from_ids = tf.keras.layers.StringLookup(
            vocabulary=CharMapping.ids_from_chars.get_vocabulary(), invert=True, mask_token=None)

    vocab_size = len(CharMapping.ids_from_chars.get_vocabulary())

    # This is the step that will change each time
    text = text[ start_index : stop_index ]

    all_ids = CharMapping.ids_from_chars(tf.strings.unicode_split(text, 'UTF-8'))
    ids_dataset = tf.data.Dataset.from_tensor_slices(all_ids)
    sequences = ids_dataset.batch(SEQ_LENGTH+1, drop_remainder=True)
    dataset = sequences.map(split_input_target)
    dataset = (dataset
                .shuffle(BUFFER_SIZE)
                .batch(BATCH_SIZE, drop_remainder=True)
                .prefetch(tf.data.experimental.AUTOTUNE))

    return dataset, vocab_size


def prepare_new_model(vocab_size):
    """
    Create and configure a new text generation model for training.

    This function instantiates a CustomTraining model with the specified
    vocabulary size and configures it with loss function, optimizer, and
    custom learning rate.

    Args:
        vocab_size (int): Size of the character vocabulary

    Returns:
        CustomTraining: Configured model ready for training with:
            - SparseCategoricalCrossentropy loss (from logits)
            - Adam optimizer with custom learning rate
            - Embedding dimension: EMBEDDING_DIM
            - RNN units: RNN_UNITS
    """
    model = CustomTraining(
                vocab_size=vocab_size,
                embedding_dim=EMBEDDING_DIM,
                rnn_units=RNN_UNITS)

    loss = tf.losses.SparseCategoricalCrossentropy(from_logits=True)
    model.compile(optimizer='adam', loss=loss)

    # Decrease the learning rate
    K.set_value(model.optimizer.learning_rate, LEARNING_RATE)

    return model

