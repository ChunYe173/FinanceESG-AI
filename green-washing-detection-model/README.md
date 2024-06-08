
# Greenwashing Detection Model

## Introduction

Our research identifies that companies across North America and the European Union often prioritize certain metrics to secure high ESG scores, aligning with the sustainability guidelines recommended by the United Nations. The Greenwashing Detection Model, powered by 82.5 million parameters sourced from Climatebert's data and research, is at the forefront of open-source tools for assessing environmental claims. The core challenge we faced was verifying the authenticity of these sustainability claims.

By employing a comprehensive English text corpus and a dataset annotated by experts, our model has demonstrated exceptional greenwashing detection capabilities, utilizing semantic search techniques. We have meticulously annotated approximately 200 data points, with a focus on industries prone to greenwashing, such as the oil sector, and have further trained the model on over 3,000 real-world environmental claims.

Dataset (https://huggingface.co/datasets/climatebert/environmental_claims).

### Model Architecture and Data

- **Parameters**: The model comprises 82.5 million parameters derived from Climatebert data and research.
- **Fine-Tuning**: Fine-tuned using the ETH Zurich dataset with a focus on the oil industry.
- **Semantic Search**: Demonstrated robust greenwashing detection capabilities using semantic search techniques.

### Experimentation and Results

- **Dataset Utilization**: The ETH Zurich dataset was instrumental in fine-tuning our BERT-based model.
- **Model Iterations**: Conducted multiple iterations (2-3) guided by comprehensive accuracy evaluations.
- **Synthetic Data Augmentation**: Generated 160 synthetic instances to enhance our dataset.

### Accuracy Metrics

- **Support Vector Classifier (SVC)**: Achieved a baseline accuracy of 75.1% on the validation dataset.
- **TF-IDF Support Vector Machine (SVM)**: Accuracy peaked at 84.2%.
- **n-gram Baseline Model**: Reached an impressive accuracy of 86%.

### Model Selection: SVC, SVM, and n-gram Models

For text classification prediction, we selected SVC, SVM, and n-gram baseline models due to the reason below:

#### Support Vector Classifier (SVC)
- **Handling High-Dimensional Data**: SVC is adept at managing high-dimensional spaces, making it ideal for text data which is sparse and high-dimensional.
- **Binary Classification**: As greenwashing detection is a binary classification problem (genuine vs. deceptive claims), SVC's ability to find the optimal hyperplane that maximizes the margin between classes is useful.

#### TF-IDF Support Vector Machine (SVM)
- **Feature Extraction**: TF-IDF vectorization is used to convert text data into numerical features. This technique weighs the importance of words, reducing the impact of common words and highlighting significant ones.
- **Effective Classification**: SVM combined with TF-IDF, enhances the model's ability to classify text by understanding the frequency and importance of words in the context of the documents.
- **Scalability**: SVM is scalable and works well with large datasets, making it suitable for processing extensive textual data from diverse sources.

#### n-gram Baseline Model
- **Contextual Understanding**: The n-gram model captures the context and sequential nature of words by considering word combinations rather than individual words. This is crucial for detecting greenwashing, where the meaning often depends on the word sequence.
- **Improved Accuracy**: By analyzing n-grams (bigrams, trigrams, etc.), the model can identify patterns and relationships in the text that single words might miss, leading to higher accuracy in classification.
- **Baseline Comparison**: The n-gram model serves as a robust baseline, providing a benchmark to evaluate the performance of more complex models like BERT.

## Challenges and Strategic Considerations

- **Generalization**: Tailoring the model to generalize across diverse organizational claims.
- **Data Verification**: Lack of transactional data complicates cross-referencing greenwashing detection.
- **Dataset Limitations**: Addressing gaps with synthetic data due to dataset constraints.
- **Model Complexity**: Managing the intricate nature and timing of model development.
- **Focus Expansion**: Expanding the model to include traded entities for further training and refinement.

## Conclusion

This project is set to bring transformative changes in ESG monitoring and greenwashing detection, ultimately leading to better decision-making, increased corporate transparency, and safer trade processes.





























