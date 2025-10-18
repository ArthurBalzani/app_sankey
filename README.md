# Sankey Diagram Application for Word Frequency Analysis

This application allows you to upload a CSV file containing questions and answers, and generate a Sankey diagram to visualize the frequency of the most common words in each question.

## Features

- CSV file upload
- Selection of column (question) for analysis
- Adjustment of the number of most frequent words to display
- Sankey diagram visualization of word frequency
- Table with word count

## Requirements

- Python 3.8 or higher
- Dependencies listed in `requirements.txt`

## How to Install

1. Clone or download this repository
2. Install the dependencies:

```
pip install -r requirements.txt
```

3. Run the application:

```
streamlit run app.py
```

## How to Use

1. After starting the application, upload a CSV file
2. The first two columns of the file will be ignored
3. Select the column (question) you want to analyze
4. Adjust the number of most frequent words to display
5. Click on "Generate Sankey Diagram"

## CSV File Format

The CSV file must have at least 3 columns. The first two will be ignored, and the rest will be considered as questions for analysis.

## Notes

- Very short words (less than 3 letters) are automatically filtered out
- Common words (stop words) such as articles and prepositions are removed from the analysis
- The analysis is performed only on the text of the responses in the selected column