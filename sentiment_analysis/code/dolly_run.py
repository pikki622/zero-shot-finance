import os
import torch
from instruct_pipeline_dolly import InstructionTextGenerationPipeline
from transformers import AutoModelForCausalLM, AutoTokenizer

import pandas as pd
import numpy as np
from time import time
from datetime import date


today = date.today()
seeds = [5768, 78516, 944601]

# set gpu
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
print("Device assigned: ", device)

# get model and tokenizer
tokenizer = AutoTokenizer.from_pretrained("databricks/dolly-v2-12b", padding_side="left")
model = AutoModelForCausalLM.from_pretrained("databricks/dolly-v2-12b", device_map="auto", torch_dtype=torch.bfloat16)

# get pipeline ready for instruction text generation
generate_text = InstructionTextGenerationPipeline(model=model, tokenizer=tokenizer)

# load test data
data_category = "FPB-sentiment-analysis-allagree"
for seed in [5768, 78516, 944601]: 

    # assign seed to numpy and PyTorch
    torch.manual_seed(seed)
    np.random.seed(seed) 

    start_t = time()
    test_data_path = f"../data/test/{data_category}-test-{str(seed)}.xlsx"
    data_df = pd.read_excel(test_data_path)


    sentences = data_df['sentence'].to_list()
    labels = data_df['label'].to_numpy()

    prompts_list = []
    for sen in sentences:
        prompt = "Discard all the previous instructions. Behave like you are an expert sentence sentiment classifier. Classify the following sentence into 'NEGATIVE', 'POSITIVE', or 'NEUTRAL' class. Label 'NEGATIVE' if it is corresponding to negative sentiment, 'POSITIVE' if it is corresponding to positive sentiment, or 'NEUTRAL' if the sentiment is neutral. Provide the label in the first line and provide a short explanation in the second line. The sentence: " + sen
        prompts_list.append(prompt)

    res = generate_text(prompts_list)

    output_list = [
        [labels[i], sentences[i], res[i][0]['generated_text']]
        for i in range(len(res))
    ]
    results = pd.DataFrame(output_list, columns=["true_label", "original_sent", "text_output"])
    time_taken = int((time() - start_t)/60.0)
    results.to_csv(f'../data/llm_prompt_outputs/dolly_{seed}_{today.strftime("%d_%m_%Y")}_{time_taken}.csv', index=False)
