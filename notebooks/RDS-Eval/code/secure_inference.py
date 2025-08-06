
import os
from pathlib import Path
from sys import exit

import pandas as pd

DATA_DIR = os.environ["DATA_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]

model_folder, prompt_path = [ str(Path(path).resolve()) for path in  DATA_DIR.split(",")]
output_path = Path(OUTPUT_DIR) / "output.txt"


# third party
from transformers import AutoModelForCausalLM
from transformers import AutoTokenizer

model = AutoModelForCausalLM.from_pretrained(model_folder)
tokenizer = AutoTokenizer.from_pretrained(model_folder)
pad_token_id = (
    tokenizer.pad_token_id
    if tokenizer.pad_token_id
    else tokenizer.eos_token_id
)

def inference(prompt: str, raw=False, **kwargs) -> str:
    input_ids = tokenizer(prompt, return_tensors="pt").input_ids
    gen_tokens = model.generate(
        input_ids,
        do_sample=True,
        temperature=0.9,
        max_length=100,
        pad_token_id=pad_token_id,
        **kwargs,
    )
    if raw:
        return gen_tokens
    else:
        gen_text = tokenizer.batch_decode(gen_tokens)[0]
        return gen_text

prompt_paths = list(Path(prompt_path).glob("*.txt"))  # list of txt files
prompts = []

for file_path in prompt_paths:
    with open(file_path, "r", encoding="utf-8") as f:
        prompts.extend(line.strip() for line in f)

# run inference & save
outputs = []
for prompt in prompts:
    print(f"Runing inference on prompt: {prompt}")
    output = inference(prompt)
    outputs.append(output)

output_path.write_text("\n\n".join(outputs) + "\n", encoding="utf-8")
print(f"Saved {len(outputs)} outputs to {output_path}")
