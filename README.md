# MovieLens Dashboard

Interactive Streamlit dashboard to analyze MovieLens (200k) ratings.

## Project structure
movielens-dashboard/
├── app.py # Main Streamlit app
├── data_processor.py # Data cleaning & aggregation
├── examine_data.py # Exploratory Data Analysis (EDA)
├── helper_Functions.py # Helper functions (incl. zip->state)
├── README.md
├── requirements.txt
└── data/
└── movie_ratings.csv



## Setup (local)
1. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate   # macOS / Linux
   venv\Scripts\activate      # Windows

pip install -r requirements.txt
streamlit run app.py