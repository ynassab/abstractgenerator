from _221230_utils import *

dataset, vocab_size = generate_dataset(0, 1)

model = prepare_new_model(vocab_size)

model.load_weights(f'training_checkpoints_12/ckpt_20')

for _ in range(5):
	model.generate_text()

