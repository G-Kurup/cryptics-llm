# cryptics-llm
Fine-tuning an LLM (T5-small) to solve cryptic crosswords

## Contents

This repo contains:
1. `scrape_guardian.py`       -- A python script to scrape and collect cryptic and quick cryptic crossword clues and answers from The Guardian.
2. `cryptics_finetune.ipynb`  -- A notebook that was used to train T5-small to solve cryptic crosswords.
3. `cryptics_tester.ipynb`    -- A notebook used for testing the fine-tuned models.
4. `few_shot_chatgpt.ipynb`   -- A notebook that tests ChatGPT 3.5 turbo on cryptic crosswords with few-shot learning.
5. `Data/cryptic_full.json`   -- A json file that contains 169,993 cryptic crossword clues and answers from The Guardian.
6. `Data/quiptic_full.json`   -- A json file that contains 36,274 quick cryptic crossword clues and answers from The Guardian.
7. `Data/Primer.pdf`          -- A primer on cryptic crosswords that I wrote, which is useful for beginners.
8. `Data/*.svg`               -- Plots of evolution of training metrics saved from tensorboard. 
   
## Background:

Cryptic crosswords are crossword puzzles that combine elements of normal/definitional crosswords with wordplay elements. Cryptics are hugely popular in Commonwealth countries (they originated in the UK), and also enjoy a not insignificant audience in the US. A standard clue* contains a wordplay part and a definition part, both of which point to a single answer. This makes the answers almost always unique, unlike plain crosswords where there could be multiple possible answers and one needs crossing letters to solve unambiguously. Good clues also tend to trick the solver by integrating the wordplay elements and definitions into a misleading 'surface' reading of the clues. Creating a 'surface' that makes sense, while following all the rules of cryptic crosswords, while also being fair to the solver, is a challenge for amateur constructors like me. Most crosswords follow "Ximenean" rules - standards widely accepted in clue construction - but there are notable setters who break these.

\* with some exceptions, such as _cryptic definitions_, _double definitions_ and _&lits_.

An example of a cryptic crossword clue and answer:   _Bird is cowardly, about to fly away. (5)_   
The answer is RAVEN, which means “bird”, and is = CRAVEN (“cowardly”) - C (the abbreviation for circa or “about”).

Because of the complicated wordplay elements involved, they are quite challenging to solve even for humans. Large Language Models struggle quite a bit to grasp the concept, especially since a well constructed clue gives no indication of which part of the clue is wordplay and which part is definitional. The surface reading can point to a completely irrelevant answer as well. Solving a clue involves multiple steps of manipulating letters ('anno' or annotation in the crossword community) and comparing definitions with words in the clue, which is difficult for a model trained to predict the next token given a sequence. Even worse, LLMs I have tested often do not adhere to the number of letters requirement in the clue ('enum' as it is usually called), and give answers with the wrong number of letters. This is not surprising, since LLMs are usually trained on tokens and not characters. I have not yet tested if a model like ByT5 will perform better in this task.

P.S. - There are a couple of other cryptic crossword datasets available online, which probably have some intersection with the dataset that I made. See [George Ho's dataset](https://cryptics.georgeho.org/) and [cryptonite](https://huggingface.co/datasets/cryptonite).
  
## Details

The Guardian publishes cryptic and 'quiptic' (easier cryptic) crosswords daily, and you can solve them on their website for free. The python script scrapes The Guardian website for cryptic clues and answers, and writes them to a json file in a format that works well with HuggingFace's `Dataset` library. It also splits the dataset into train and test subsets using methods in the `Datasets` library. To make the dataset yourself, run the script as: 

      python3 scrape_guardian.py crossword_no /path/to/output/directory

where `crossword_no: int` is the latest crossword number on the Guardian website that you would like to start scraping from, and `/path/to/output/directory` is the path to the directory where you want the dataset created.

Both `cryptics_finetune.ipynb` and `cryptics_tester.ipynb` were both run on Google Colab on A100 GPUs. It should take less than an hour to train T5-small for 30 epochs. T5-small was finetuned using HuggingFace's `Transformers` library, and it automatically saves the checkpoint with the best evaluation metrics on the validation set.

I gave the model some help in finding the answer in the testing phase, by generating a few possible answers and picking the most probable answer that fits the number of letters. This helped a bit with accuracy, as the model does not always get the right number of letters (although it seems to consistently be in the ball park!). However, this made the testing process significantly slower, and you can turn off this feature by setting `num_beams=1` in the generation config in the notebook.

The notebook `few_shot_chatgpt.ipynb` uses ChatGPT API calls to test the model on crosswords from the same cryptics dataset. Few-shot learning was done with the same 25 solved examples (randomly chosen from the training set) given as context for each test. A total of 500 test examples were used, which were sampled from the cryptics test dataset.

## Results

Two models were trained on cryptics and quiptics respectively. The quiptic dataset is much smaller, but has "easier" clues. The cryptic dataset is much bigger, and has moderately difficult clues.
1. The quiptic model achieved an accuracy of __just 6%__ on the quiptic test set. I did not bother with testing it on the cryptics dataset.
2. The cryptic model achieved an accuracy of __18.4%__ on the cryptics test set and __13.7%__ on the quiptics test set. Training on more crossword clues clearly makes the model better at solving them.
3. For comparison, few-shot learning with ChatGPT 3.5 turbo (a much bigger model) produced __10%__ accuracy. 

Notably, the cryptic model, which is better at solving crosswords overall, did worse on the easier quiptic crosswords. This makes sense as it was trained on a different distribution than the test distribution, but it is interesting that it struggled more with clues that are meant to be easier for humans.

## Training Plots:

Training Loss:

<img src="https://github.com/G-Kurup/cryptics-llm/blob/main/Data/train_loss.svg" alt="Train loss" width="500"/>

Validation Loss:

<img src="https://github.com/G-Kurup/cryptics-llm/blob/main/Data/eval_loss.svg" alt="Validation loss" width="500"/>

Learning Rate Decay:

<img src="https://github.com/G-Kurup/cryptics-llm/blob/main/Data/train_learning_rate.svg" alt="Learning rate" width="500"/>

