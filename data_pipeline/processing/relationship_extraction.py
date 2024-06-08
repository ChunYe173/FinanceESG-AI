
from corenlp import triplet_extraction

model_id = "TheBloke/wizardLM-7B-HF"
hf_auth = "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"
triplet_extractor = triplet_extraction.EsgTripletExtraction(model_id, hf_auth)
# Choose the list of stop words where model might stop hallucinating.
stop_list = ['\nHuman:', '\n```\n']

triplet_extractor.make_extraction_chain(stop_list)

#choose either a single text to extract triplet
input_text = "In accordance with our ambitious goal, the water withdrawal of the data\
              center decreased remarkably from 3.874 million litres to 2.367 million litres across\
              the past three years."


output_one = triplet_extractor.extract_triplets(input_text)

print(output_one)