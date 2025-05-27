import training_utils

MODEL_WEIGHTS_PATH = f'training_checkpoints_12/ckpt_20'

if __name__ == "__main__":
	dataset, vocab_size = training_utils.generate_dataset(0, 1)
	model = training_utils.prepare_new_model(vocab_size)
	model.load_weights(MODEL_WEIGHTS_PATH)

	for _ in range(5):
		model.generate_text()

