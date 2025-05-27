import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'  # Turn off info messages
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
    # Force me to set the checkpoint_dir each time to avoid overwriting
    checkpoint_prefix = os.path.join(checkpoint_dir, 'ckpt_{epoch}')
    checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
                filepath=checkpoint_prefix,
                save_weights_only=True)
    return checkpoint_callback


def split_input_target(sequence):
    input_text = sequence[:-1]
    target_text = sequence[1:]
    return input_text, target_text


class CharMapping():
    pass


class MyModel(tf.keras.Model):
    def __init__(self, vocab_size, embedding_dim, rnn_units):
        super().__init__(self)
        self.embedding = tf.keras.layers.Embedding(vocab_size, embedding_dim)
        self.gru = tf.keras.layers.GRU(rnn_units,
                                        return_sequences=True,
                                        return_state=True)
        self.dense = tf.keras.layers.Dense(vocab_size)

    def call(self, inputs, states=None, return_state=False, training=False):
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
    @tf.function
    def train_step(self, inputs):
        inputs, labels = inputs
        with tf.GradientTape() as tape:
            predictions = self(inputs, training=True)
            loss = self.loss(labels, predictions)
        grads = tape.gradient(loss, self.trainable_variables)
        self.optimizer.apply_gradients(zip(grads, self.trainable_variables))
        return {'loss': loss}


class OneStep(tf.keras.Model):
    def __init__(self, model, chars_from_ids, ids_from_chars, temperature=1.0):
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


def generate_dataset(start_index, stop_index, path_to_file = 'abstracts.txt'):
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
    model = CustomTraining(
                vocab_size=vocab_size,
                embedding_dim=EMBEDDING_DIM,
                rnn_units=RNN_UNITS)

    loss = tf.losses.SparseCategoricalCrossentropy(from_logits=True)
    model.compile(optimizer='adam', loss=loss)

    # Decrease the learning rate
    K.set_value(model.optimizer.learning_rate, LEARNING_RATE)

    return model

