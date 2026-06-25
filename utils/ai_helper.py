import os
import json
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

class CategoryPredictor:
    def __init__(self):
        self.contoh_barang = []
        self.kategori_barang = []
        self._load_dataset()
        
        self.vectorizer = CountVectorizer()
        self.model = MultinomialNB()
        self._train_model()

    def _load_dataset(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, "training_data.json")
        try:
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        self.contoh_barang.append(item["nama"])
                        self.kategori_barang.append(item["kategori"])
            else:
                # Fallback dataset jika file hilang
                self.contoh_barang = ["Laptop", "Meja", "Pena"]
                self.kategori_barang = ["Elektronik", "Furnitur", "Alat Tulis"]
        except:
            self.contoh_barang = ["Laptop", "Meja", "Pena"]
            self.kategori_barang = ["Elektronik", "Furnitur", "Alat Tulis"]

    def _train_model(self):
        X = self.vectorizer.fit_transform(self.contoh_barang)
        self.model.fit(X, self.kategori_barang)

    def predict_category(self, nama_barang):
        """Predict category based on item name"""
        if not nama_barang.strip():
            return "Lainnya"
        try:
            X_test = self.vectorizer.transform([nama_barang])
            prediksi = self.model.predict(X_test)
            return prediksi[0]
        except:
            return "Lainnya"