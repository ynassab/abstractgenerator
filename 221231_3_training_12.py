from _221230_utils import *
from time import sleep


if __name__ == "__main__":
	
	# using the same charset as era 11
	start_index = 0
	stop_index  = 100000000
	current_iteration = 12
	reference_iteration = 11
	best_checkpoint = 20
		
	dataset, vocab_size = generate_dataset(start_index=start_index, stop_index=stop_index)
	
	model = prepare_new_model(vocab_size) # note vocab_size is constant; 109

	# load best model from previous iteration
	if reference_iteration != -1:
		model.load_weights(f'training_checkpoints_{reference_iteration}/ckpt_{best_checkpoint}')
	
	# manually set the checkpoint dir each time; be careful to avoid overwriting past checkpoints
	checkpoint_callback = set_new_checkpoint_callback(checkpoint_dir=f'training_checkpoints_{current_iteration}')
	model.fit(dataset, epochs=EPOCHS, callbacks=[checkpoint_callback])
		
	for _ in range(5):
		model.generate_text()

