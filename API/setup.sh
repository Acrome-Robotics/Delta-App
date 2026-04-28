#!/bin/bash

# Raspberry Pi icin Otomatik Kurulum ve CLI (Komut Satiri) Araci

echo "=========================================="
echo " Acrome Delta API Kurulumuna Hosgeldiniz "
echo "=========================================="

# Bulundugumuz dizini al
API_DIR=$(pwd)

# 1. Sanal ortam (venv) olusturuluyor
echo "[1/3] Sanal ortam (venv) olusturuluyor..."
python3 -m venv venv

# 2. Gerekli kutuphanelerin kurulumu
echo "[2/3] Gerekli Python kutuphaneleri yukleniyor..."
source venv/bin/activate
pip install -r requirements.txt


# 3. Global 'delta' komutunun olusturulmasi
echo "[3/3] 'delta' global komutu Linux sistemine entegre ediliyor..."

# /usr/local/bin altina 'delta' adinda bir calistirilabilir dosya (script) yaziyoruz
cat <<EOF | sudo tee /usr/local/bin/delta > /dev/null
#!/bin/bash
if [ "\$1" == "api" ] && [ "\$2" == "start" ]; then
    echo "Acrome Delta API baslatiliyor..."
    cd "$API_DIR"
    $API_DIR/venv/bin/python3 app.py
elif [ "\$1" == "api" ] && [ "\$2" == "service-install" ]; then
    echo "Sistem servisi kuruluyor (Otomatik baslatma)..."
    sudo cp $API_DIR/delta_api.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable delta_api.service
    sudo systemctl start delta_api.service
    echo "Servis kuruldu. Artik arkada otomatik calisacak."
elif [ "\$1" == "api" ] && [ "\$2" == "service-stop" ]; then
    sudo systemctl stop delta_api.service
    sudo systemctl disable delta_api.service
    echo "Servis durduruldu ve otomatik baslatma kapatildi."
else
    echo "=========================================="
    echo " Acrome Delta Kontrol Merkezi"
    echo "=========================================="
    echo "Kullanim:"
    echo "  delta api start             : API'yi bu terminalde hemen calistirir."
    echo "  delta api service-install   : API'yi arkaplan servisi yapar (Her acilista otomatik baslar)."
    echo "  delta api service-stop      : Arkaplan servisini kapatir."
    echo ""
fi
EOF

# Olusturulan dosyaya calistirma yetkisi ver
sudo chmod +x /usr/local/bin/delta

echo ""
echo "=========================================="
echo " KURULUM BASARIYLA TAMAMLANDI! 🎉"
echo "=========================================="
echo "Artik terminalin neresinde olursaniz olun sadece su komutu yazarak API'yi calistirabilirsiniz:"
echo ""
echo "    delta api start"
echo ""
