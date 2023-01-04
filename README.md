# arxiv-ml
Article dataset provided courtesy of ArXiv (operated by Cornell University) on Kaggle under a CC0 Public Domain license.
https://www.kaggle.com/datasets/Cornell-University/arxiv

## How the model was built
The model here, for which the weights are saved in `./training_checkpoints_12/ckpt_20`, was trained for 240 epochs until the sparse categorical cross-entropy (SCC) loss converged to the second decimal place (or, more accurately, that the second demical place would remain static for at least 100 more epochs).

The model is a Recurrent Neural Network (RNN) comprised of, in sequence, an Embedding layer with dimension 256, a Gated Recurrent Unit (GRU) with dimension 1024, and a dense layer as output, which contains one neuron for each character that may be generated (here, 109). A slow learning rate of 0.0001 was used to maintain stability during training.

## Usage
Not all files are included in this repository for neatness, but those of interest are included. `221231_3_training_12.py` is the twelfth iteration of 20 epochs that were used to train the algorithm, and `230103_generate_text.py` may be run by the user to generate text using the trained model.

Below is an example of text that the algorithm produces. Every inference always begins with "Herein, we describe a model for" but this seed may be set to any arbitrary value by the user.

> Herein, we describe a new model for the compound fracture. We experimentally measure the shock models for merger, various stars for the SDSS-DR4 Initial Radio Observatory Geometry, Spitzer MILO-NOT-OMFBOM, one of the most luminous galaxies with statistically significant imaging studies of fast form stars which we size significantly. Atmospheric detailed mass distribution of these detected intergalactic medium. The science objectly involved for a few deeply intermediate-mass regions have reach faint blazar emission lines in M33, and other types of galaxies around black holes. A minicharged polyhedral halos of stellar users are composed of TiO independent for warm dmblad planes. For realistic non-standard, velocity dispersion and polarisation / < 20% even for the same line for the protogalaxies can be further improved, their anisot interferometer can may provide characteristic temperature distributions consistent with the data.
