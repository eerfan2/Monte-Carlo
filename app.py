import json
from flask import Flask, render_template, request, redirect, url_for
from sklearn.linear_model import LinearRegression
import random

app = Flask(__name__)

# Fungsi pembulatan dan format angka ke dua desimal
def custom_round(value, decimals=3):
    factor = 10 ** decimals
    shifted = value * factor
    integer_part = int(shifted)
    decimal_part = shifted - integer_part
    third_decimal = round(decimal_part * 10)

    if third_decimal >= 5:
        rounded = (integer_part + 1) / factor
    else:
        rounded = integer_part / factor

    return rounded

# Fungsi untuk menghasilkan deret angka acak
def generate_random_numbers(Y0, b, d, n, jumlah_kategori):
    random_numbers = [Y0]
    for i in range(1, jumlah_kategori):
        Yi = (b * random_numbers[-1] + d) % n
        random_numbers.append(Yi)
    return random_numbers

# Fungsi untuk menghitung akurasi
# Fungsi untuk menghitung akurasi tanpa angka desimal
def calculate_accuracy(actual_values, predicted_values):
    total_error = 0
    for actual, predicted in zip(actual_values, predicted_values):
        error = abs(actual - predicted)  # Menghitung error absolut
        total_error += error
    
    # Menghitung error rata-rata
    average_error = total_error / len(actual_values)
    
    # Menghitung error relatif rata-rata
    relative_error_percentage = (average_error / sum(actual_values)) * 100
    
    # Menghitung akurasi dan membulatkan ke bilangan bulat
    accuracy = 100 - relative_error_percentage
    accuracy = int(accuracy)  # Membulatkan ke bilangan bulat tanpa angka desimal
    return accuracy


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data', methods=['GET', 'POST'])
def data():
    try:
        with open('data_saved.json', 'r') as json_file:
            data_json = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        data_json = None

    return render_template('data.html', data_json=data_json)

@app.route('/simulasi', methods=['GET', 'POST'])
def simulasi():
    if request.method == 'POST':
        jumlah_kategori = int(request.form.get('jumlah_kategori'))
        tahun = int(request.form.get('tahun'))
        
        permintaan = []
        frekuensi = []
        for i in range(jumlah_kategori):
            permintaan.append(request.form.get(f'kategori_{i}_nama'))
            frekuensi.append(int(request.form.get(f'kategori_{i}_frekuensi')))

        total_frekuensi = sum(frekuensi)
        distribusi_probabilitas = [custom_round(f / total_frekuensi, 3) for f in frekuensi]

        total_probabilitas = sum([float(p) for p in distribusi_probabilitas])
        if total_probabilitas < 1:
            distribusi_probabilitas[-1] = custom_round(float(distribusi_probabilitas[-1]) + (1 - total_probabilitas), 3)

        distribusi_kumulatif = []
        kumulatif = 0
        for dp in distribusi_probabilitas:
            kumulatif += dp
            distribusi_kumulatif.append(custom_round(kumulatif, 3))

        interval = []
        start = 1
        total_length = 100
        for i in range(len(distribusi_kumulatif)):
            end = round(distribusi_kumulatif[i] * total_length)
            if i > 0:
                start = round(distribusi_kumulatif[i-1] * total_length) + 1
            interval.append(f"{start}-{end}")
            start = end + 1

        # Generate deret angka acak
        Y0 = 10  # Nilai awal
        b = 2     # Faktor pengali
        d = 10    # Increment
        n = 95    # Modulus
        random_numbers = generate_random_numbers(Y0, b, d, n, jumlah_kategori)

        hasil = list(zip(permintaan, frekuensi, distribusi_probabilitas, distribusi_kumulatif, interval, random_numbers))

        # Menyimpan data JSON
        data_json = {
            "tahun": tahun,
            "jumlah_kategori": jumlah_kategori,
            "kategori": [
                {
                    "nama": permintaan[i],
                    "frekuensi": frekuensi[i],
                    "distribusi_probabilitas": distribusi_probabilitas[i],
                    "distribusi_kumulatif": distribusi_kumulatif[i],
                    "interval": interval[i],
                    "random_number": random_numbers[i]
                }
                for i in range(jumlah_kategori)
            ]
        }

        # Simulasi nilai prediksi untuk akurasi
        # Misalnya, kita ingin memprediksi jumlah tamu menginap berdasarkan beberapa data frekuensi yang ada
        actual_values = [random.choice(frekuensi) for _ in range(jumlah_kategori)]  # Misal ini adalah data aktual
        predicted_values = random_numbers  # Gunakan nilai acak sebagai prediksi

        accuracy = calculate_accuracy(actual_values, predicted_values)  # Hitung akurasi

        # Menambahkan nilai akurasi ke dalam data_json
        data_json['akurasi'] = accuracy

        # Menyimpan data ke dalam file JSON
        with open('data.json', 'w') as json_file:
            json.dump(data_json, json_file, indent=4)

        return render_template('hasil.html', hasil=hasil, data_json=data_json, accuracy=accuracy)

    return render_template('simulasi.html')

@app.route('/hasil')
def hasil():
    try:
        with open('data.json', 'r') as json_file:
            data_json = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        data_json = None

    return render_template('hasil.html', data_json=data_json)

@app.route('/simpan_hasil_simulasi', methods=['POST'])
def simpan_hasil_simulasi():
    try:
        with open('data.json', 'r') as json_file:
            data_json = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        data_json = None

    if not data_json:
        return redirect(url_for('hasil'))

    with open('data.json', 'w') as json_file:
        json.dump(data_json, json_file, indent=4)

    return redirect(url_for('hasil'))

@app.route('/simpan_riwayat', methods=['POST'])
def simpan_riwayat():
    try:
        with open('data.json', 'r') as json_file:
            data_json = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        data_json = None

    if not data_json:
        return redirect(url_for('hasil'))

    save_file = 'data_saved.json'

    try:
        with open(save_file, 'r') as json_file:
            existing_data = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []

    existing_data.append(data_json)

    with open(save_file, 'w') as json_file:
        json.dump(existing_data, json_file, indent=4)

    return redirect(url_for('data'))

@app.route('/delete_item/<int:index>', methods=['POST'])
def delete_item(index):
    try:
        with open('data.json', 'r') as json_file:
            data_json = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        data_json = None

    if data_json:
        del data_json['kategori'][index]  # Menghapus item berdasarkan index
        with open('data.json', 'w') as json_file:
            json.dump(data_json, json_file, indent=4)

    return redirect(url_for('hasil'))

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    print(app.url_map)  # Log endpoint yang terdaftar
    app.run(debug=True)
