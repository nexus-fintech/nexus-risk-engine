import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# --- Configuration Constants ---
DATASET_FILE = 'nexus_credit_data.xlsx'
MODEL_OUTPUT_FILE = 'nexus_risk_model.pkl'
RANDOM_STATE = 42
TEST_SIZE = 0.2
N_ESTIMATORS = 100

def train_model():
    """
    Loads credit data, trains a Random Forest Classifier, and serializes the model.
    """
    print(f"--- Starting Training Pipeline ---")
    
    # 1. Load Data
    print(f"[1/5] Loading dataset from {DATASET_FILE}...")
    try:
        df = pd.read_excel(DATASET_FILE)
    except FileNotFoundError:
        print(f"Error: The file {DATASET_FILE} was not found.")
        return

    # Data Cleaning: Strip whitespace from headers and drop null rows
    df.columns = df.columns.str.strip()
    initial_count = len(df)
    df = df.dropna()
    print(f"      Data loaded. Rows: {len(df)} (Dropped {initial_count - len(df)} null rows).")

    # 2. Define Features and Target
    # These must match the columns in the Excel file exactly
    features = [
        'monthly_income', 
        'requested_amount', 
        'term_in_months', 
        'age', 
        'monthly_debt'
    ]
    target = 'loan_status'

    print(f"[2/5] Selecting features: {features}")
    
    X = df[features]
    y = df[target]

    # Display sample for verification
    print(f"      Sample input data:\n{X.head()}")

    # 3. Split Data
    print(f"[3/5] Splitting data (Train: {100*(1-TEST_SIZE):.0f}% / Test: {100*TEST_SIZE:.0f}%)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )

    # 4. Train Model
    print(f"[4/5] Training Random Forest Classifier (n_estimators={N_ESTIMATORS})...")
    model = RandomForestClassifier(n_estimators=N_ESTIMATORS, random_state=RANDOM_STATE)
    model.fit(X_train, y_train)

    # 5. Evaluate Model
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    print(f"[5/5] Evaluation complete. Model Accuracy: {accuracy * 100:.2f}%")

    # 6. Serialize Model
    joblib.dump(model, MODEL_OUTPUT_FILE)
    print(f"--- Success! Model saved to: {MODEL_OUTPUT_FILE} ---")

    # 7. ANALYTICAL DATASET GENERATION (For Power BI)
    print("--- Generating Dataset for Business Intelligence ---")

    # We use the entire dataset (X) to simulate how the model would score it
    all_predictions_prob = model.predict_proba(X)[:, 1]  # Approval probability

    # We replicate YOUR exact business logic
    df_analytics = df.copy()
    df_analytics['Approval_Probability'] = all_predictions_prob

    # Exact formula from your Service: 300 + (Prob * 550)
    df_analytics['AI_Score'] = (300 + (df_analytics['Approval_Probability'] * 550)).astype(int)

    # Risk Classification (Your logic)
    def get_risk_level(score):
        if score >= 750: 
            return 'LOW'
        elif score >= 650: 
            return 'MEDIUM'
        return 'HIGH'

    df_analytics['Risk_Level'] = df_analytics['AI_Score'].apply(get_risk_level)

    # Save new file
    OUTPUT_CSV = 'nexus_bi_data.csv'
    df_analytics.to_csv(OUTPUT_CSV, index=False)
    print(f"--- [BI] File successfully generated: {OUTPUT_CSV} ---")


if __name__ == "__main__":
    train_model()