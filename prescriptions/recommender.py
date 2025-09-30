import pickle
import pandas as pd
from difflib import get_close_matches
import os

# --- Data Loading (Crucial Section for Fix) ---
# NOTE: Please verify the paths ('new_data.pkl', 'similarity.pkl') are correct 
# relative to where recommender.py is located.

new_data = pd.DataFrame()
similarity = None
IS_READY = False

try:
    # Get the directory of the current script
    base_dir = os.path.dirname(__file__)
    # CORRECTED: Join with 'data' subdirectory for correct path
    data_path = os.path.join(base_dir, 'data', 'medicines.pkl')
    similarity_path = os.path.join(base_dir, 'data', 'similarity.pkl')

    with open(data_path, 'rb') as f:
        data_obj = pickle.load(f)
    
    # FIX: Check if the loaded object is a dictionary and convert it to a DataFrame.
    # This prevents the 'dict' object has no attribute 'astype' error.
    if isinstance(data_obj, dict):
        new_data = pd.DataFrame(data_obj)
        print("INFO: Loaded dictionary data was successfully coerced into a DataFrame.")
    elif isinstance(data_obj, pd.DataFrame):
        new_data = data_obj
    else:
        # Fallback for unexpected types
        new_data = pd.DataFrame(data_obj)
        print(f"WARNING: Loaded data object type ({type(data_obj)}) was unexpected. Coerced to DataFrame.")


    with open(similarity_path, 'rb') as f:
        similarity = pickle.load(f)

    IS_READY = True
    
except FileNotFoundError:
    print("ERROR: Data files (new_data.pkl or similarity.pkl) not found. Recommendation service disabled.")
except Exception as e:
    print(f"ERROR during data loading for recommender: {e}")

# --- Recommender Function ---

def get_recommendations(medicine_name, k=5):
    """
    Retrieves recommended medicines based on the input medicine name using 
    a pre-calculated similarity matrix.
    
    :param medicine_name: The name of the medicine to find recommendations for.
    :param k: The number of recommendations to return (default is 5).
    :return: A list of dictionaries containing the recommended medicine name 
             and its similarity score, or an empty list if data is not ready 
             or no match is found.
    """
    
    # Ensure the engine is initialized and data is valid
    if not IS_READY or new_data.empty or similarity is None:
        print("ERROR: Recommendation engine is not initialized or data is missing.")
        return []

    # Validate the necessary column exists
    if 'Drug_Name' not in new_data.columns:
        print("ERROR: 'Drug_Name' column not found in data.")
        return []

    # Line 57 (Original location of error): Now this is safe because new_data is a DataFrame.
    df_drugs = new_data['Drug_Name'].astype(str).tolist()
    
    # 1. Find the closest matching medicine name
    closest_match = get_close_matches(medicine_name, df_drugs, n=1, cutoff=0.6)

    if not closest_match:
        print(f"INFO: No close match found for '{medicine_name}'.")
        return []

    medicine_match = closest_match[0]
    
    # 2. Get the index of the matching medicine
    try:
        # Use .loc[] for reliable index lookup
        index = new_data.loc[new_data['Drug_Name'] == medicine_match].index[0]
    except IndexError:
        print(f"ERROR: Could not find index for matched medicine: {medicine_match}")
        return []
    
    # 3. Get similarity scores and sort
    distances = similarity[index]
    
    # If the similarity is a sparse matrix row (e.g., from TfidfVectorizer output), 
    # ensure it's converted to a dense array for sorting
    if hasattr(distances, 'toarray'):
         distances = distances.toarray()[0]
        
    # Create a list of (index, distance) tuples and sort (excluding the medicine itself)
    med_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:k+1] 

    recommendations = []
    
    # 4. Extract recommended medicine names
    for i in med_list:
        recommended_index = i[0]
        similarity_score = i[1]

        # Use iloc to get the row by index and extract 'Drug_Name'
        recommended_medicine = new_data.iloc[recommended_index]['Drug_Name']
        
        recommendations.append({
            'name': recommended_medicine,
            'similarity': float(similarity_score) 
        })
        
    return recommendations
