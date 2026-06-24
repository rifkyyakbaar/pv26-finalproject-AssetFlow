from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

class CategoryPredictor:
    def __init__(self):
        self.contoh_barang = [
            "Laptop Asus", "Mouse Logitech", "Keyboard Mekanikal", "Monitor LG", "Proyektor Epson", "Kabel HDMI",  # Elektronik
            "Meja Kayu", "Kursi Kantor", "Lemari Besi", "Rak Buku", "Papan Tulis",                               # Furnitur
            "Spidol Marker", "Kertas HVS", "Pena Bolpoin", "Stapler", "Buku Catatan", "Tinta Printer"            # Alat Tulis
        ]
        self.kategori_barang = [
            "Elektronik", "Elektronik", "Elektronik", "Elektronik", "Elektronik", "Elektronik",
            "Furnitur", "Furnitur", "Furnitur", "Furnitur", "Furnitur",
            "Alat Tulis", "Alat Tulis", "Alat Tulis", "Alat Tulis", "Alat Tulis", "Alat Tulis"
        ]
        
        self.vectorizer = CountVectorizer()
        self.model = MultinomialNB()
        self._train_model()

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