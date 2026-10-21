import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "locales"

EN = {
    "convert.preset_h264": "H.264 MP4 (compatible)", "convert.preset_h265": "H.265 MP4 (smaller)",
    "convert.preset_av1": "AV1 MKV (smallest)", "convert.preset_proxy": "720p H.264 proxy",
    "convert.preset_remux": "Remux to MKV (no re-encoding)", "convert.resolution_source": "Keep source resolution",
    "convert.resolution_1080p": "1080p", "convert.resolution_720p": "720p",
    "convert.engine_automatic": "Automatic (recommended)", "convert.engine_software": "Software / CPU",
    "convert.status_ready": "Ready", "convert.status_skipped": "Skipped",
    "convert.status_unknown_resolution": "Unknown resolution", "convert.status_converting": "Converting",
    "convert.status_passed": "Passed", "convert.status_cancelled": "Cancelled", "convert.status_failed": "Failed",
    "choice.system": "System", "choice.light": "Light", "choice.dark": "Dark", "choice.high_contrast": "High contrast",
    "choice.selected": "Selected", "choice.visible": "Visible", "choice.all_scanned": "All scanned",
    "choice.copy": "Copy", "choice.move": "Move", "choice.any": "Any", "choice.images": "Images", "choice.videos": "Videos",
    "choice.quiet": "Quiet", "choice.balanced": "Balanced", "choice.fast": "Fast",
}

OVERRIDES = {
    "zh-CN": ["H.264 MP4（兼容）","H.265 MP4（更小）","AV1 MKV（最小）","720p H.264 代理","重新封装为 MKV（不重新编码）","保持源分辨率","自动（推荐）","软件 / CPU","就绪","已跳过","未知分辨率","正在转换","已完成","已取消","失败","系统","浅色","深色","高对比度","已选择","可见","全部已扫描","复制","移动","任意","图像","视频","安静","均衡","快速"],
    "nl": ["H.264 MP4 (compatibel)","H.265 MP4 (kleiner)","AV1 MKV (kleinst)","720p H.264-proxy","Remux naar MKV (zonder hercodering)","Bronresolutie behouden","Automatisch (aanbevolen)","Software / CPU","Gereed","Overgeslagen","Onbekende resolutie","Converteren","Geslaagd","Geannuleerd","Mislukt","Systeem","Licht","Donker","Hoog contrast","Geselecteerd","Zichtbaar","Alles gescand","Kopiëren","Verplaatsen","Alles","Afbeeldingen","Video's","Rustig","Gebalanceerd","Snel"],
    "fr": ["MP4 H.264 (compatible)","MP4 H.265 (plus petit)","MKV AV1 (le plus petit)","Proxy H.264 720p","Remuxer en MKV (sans réencodage)","Conserver la résolution source","Automatique (recommandé)","Logiciel / processeur","Prêt","Ignoré","Résolution inconnue","Conversion en cours","Réussi","Annulé","Échec","Système","Clair","Sombre","Contraste élevé","Sélectionnés","Visibles","Tous analysés","Copier","Déplacer","Tous","Images","Vidéos","Silencieux","Équilibré","Rapide"],
    "de": ["H.264-MP4 (kompatibel)","H.265-MP4 (kleiner)","AV1-MKV (kleinste Datei)","720p-H.264-Proxy","In MKV umpacken (ohne Neucodierung)","Quellauflösung beibehalten","Automatisch (empfohlen)","Software / CPU","Bereit","Übersprungen","Unbekannte Auflösung","Konvertierung läuft","Erfolgreich","Abgebrochen","Fehlgeschlagen","System","Hell","Dunkel","Hoher Kontrast","Ausgewählt","Sichtbar","Alle gescannt","Kopieren","Verschieben","Beliebig","Bilder","Videos","Leise","Ausgewogen","Schnell"],
    "ja": ["H.264 MP4（互換）","H.265 MP4（小容量）","AV1 MKV（最小容量）","720p H.264 プロキシ","MKVへリマックス（再エンコードなし）","元の解像度を維持","自動（推奨）","ソフトウェア / CPU","準備完了","スキップ","解像度不明","変換中","完了","キャンセル","失敗","システム","ライト","ダーク","ハイコントラスト","選択済み","表示中","スキャン済みすべて","コピー","移動","すべて","画像","動画","静音","バランス","高速"],
    "ko": ["H.264 MP4(호환)","H.265 MP4(더 작게)","AV1 MKV(가장 작게)","720p H.264 프록시","MKV로 리먹스(재인코딩 없음)","원본 해상도 유지","자동(권장)","소프트웨어 / CPU","준비됨","건너뜀","알 수 없는 해상도","변환 중","완료","취소됨","실패","시스템","밝게","어둡게","고대비","선택됨","표시됨","전체 스캔","복사","이동","모두","이미지","동영상","저소음","균형","빠름"],
    "ru": ["H.264 MP4 (совместимый)","H.265 MP4 (меньше)","AV1 MKV (наименьший)","Прокси H.264 720p","Ремукс в MKV (без перекодирования)","Сохранить исходное разрешение","Автоматически (рекомендуется)","Программно / ЦП","Готово","Пропущено","Разрешение неизвестно","Преобразование","Успешно","Отменено","Ошибка","Системная","Светлая","Тёмная","Высокая контрастность","Выбранные","Видимые","Все просканированные","Копировать","Переместить","Любые","Изображения","Видео","Тихий","Сбалансированный","Быстрый"],
    "es": ["MP4 H.264 (compatible)","MP4 H.265 (más pequeño)","MKV AV1 (el más pequeño)","Proxy H.264 720p","Remultiplexar a MKV (sin recodificar)","Mantener la resolución de origen","Automático (recomendado)","Software / CPU","Listo","Omitido","Resolución desconocida","Convirtiendo","Completado","Cancelado","Fallido","Sistema","Claro","Oscuro","Alto contraste","Seleccionados","Visibles","Todos analizados","Copiar","Mover","Cualquiera","Imágenes","Vídeos","Silencioso","Equilibrado","Rápido"],
    "sv": ["H.264 MP4 (kompatibel)","H.265 MP4 (mindre)","AV1 MKV (minst)","720p H.264-proxy","Remuxa till MKV (utan omkodning)","Behåll källupplösning","Automatiskt (rekommenderas)","Programvara / CPU","Klar","Överhoppad","Okänd upplösning","Konverterar","Godkänd","Avbruten","Misslyckades","System","Ljust","Mörkt","Hög kontrast","Markerade","Synliga","Alla skannade","Kopiera","Flytta","Alla","Bilder","Videor","Tyst","Balanserad","Snabb"],
    "bg": ["H.264 MP4 (съвместим)","H.265 MP4 (по-малък)","AV1 MKV (най-малък)","720p H.264 прокси","Ремуксиране в MKV (без прекодиране)","Запазване на изходната резолюция","Автоматично (препоръчително)","Софтуер / CPU","Готово","Пропуснато","Неизвестна резолюция","Преобразуване","Успешно","Отказано","Неуспешно","Системна","Светла","Тъмна","Висок контраст","Избрани","Видими","Всички сканирани","Копиране","Преместване","Всички","Изображения","Видеоклипове","Тих","Балансиран","Бърз"],
    "th": ["H.264 MP4 (เข้ากันได้)","H.265 MP4 (เล็กกว่า)","AV1 MKV (เล็กที่สุด)","พร็อกซี H.264 720p","รีมัคซ์เป็น MKV (ไม่เข้ารหัสใหม่)","คงความละเอียดต้นฉบับ","อัตโนมัติ (แนะนำ)","ซอฟต์แวร์ / CPU","พร้อม","ข้ามแล้ว","ไม่ทราบความละเอียด","กำลังแปลง","สำเร็จ","ยกเลิกแล้ว","ล้มเหลว","ระบบ","สว่าง","มืด","คอนทราสต์สูง","ที่เลือก","ที่มองเห็น","ที่สแกนทั้งหมด","คัดลอก","ย้าย","ทั้งหมด","รูปภาพ","วิดีโอ","เงียบ","สมดุล","เร็ว"],
    "id": ["H.264 MP4 (kompatibel)","H.265 MP4 (lebih kecil)","AV1 MKV (paling kecil)","Proksi H.264 720p","Remux ke MKV (tanpa enkode ulang)","Pertahankan resolusi sumber","Otomatis (disarankan)","Perangkat lunak / CPU","Siap","Dilewati","Resolusi tidak diketahui","Mengonversi","Berhasil","Dibatalkan","Gagal","Sistem","Terang","Gelap","Kontras tinggi","Dipilih","Terlihat","Semua dipindai","Salin","Pindahkan","Apa saja","Gambar","Video","Senyap","Seimbang","Cepat"],
    "el": ["H.264 MP4 (συμβατό)","H.265 MP4 (μικρότερο)","AV1 MKV (μικρότερο)","Διαμεσολαβητής H.264 720p","Επαναποθήκευση σε MKV (χωρίς επανακωδικοποίηση)","Διατήρηση ανάλυσης πηγής","Αυτόματα (συνιστάται)","Λογισμικό / CPU","Έτοιμο","Παραλείφθηκε","Άγνωστη ανάλυση","Μετατροπή","Επιτυχία","Ακυρώθηκε","Απέτυχε","Σύστημα","Φωτεινό","Σκοτεινό","Υψηλή αντίθεση","Επιλεγμένα","Ορατά","Όλα τα σαρωμένα","Αντιγραφή","Μετακίνηση","Οποιοδήποτε","Εικόνες","Βίντεο","Ήσυχο","Ισορροπημένο","Γρήγορο"],
    "fil": ["H.264 MP4 (compatible)","H.265 MP4 (mas maliit)","AV1 MKV (pinakamaliit)","720p H.264 proxy","I-remux sa MKV (walang muling pag-encode)","Panatilihin ang resolution ng source","Awtomatiko (inirerekomenda)","Software / CPU","Handa","Nilaktawan","Hindi alam na resolution","Kino-convert","Matagumpay","Kinansela","Nabigo","System","Maliwanag","Madilim","Mataas na contrast","Napili","Nakikita","Lahat ng na-scan","Kopyahin","Ilipat","Anuman","Mga larawan","Mga video","Tahimik","Balansyado","Mabilis"],
    "hi": ["H.264 MP4 (संगत)","H.265 MP4 (छोटा)","AV1 MKV (सबसे छोटा)","720p H.264 प्रॉक्सी","MKV में रीमक्स (पुनः एन्कोडिंग नहीं)","स्रोत रिज़ॉल्यूशन रखें","स्वचालित (अनुशंसित)","सॉफ़्टवेयर / CPU","तैयार","छोड़ा गया","अज्ञात रिज़ॉल्यूशन","रूपांतरण जारी","सफल","रद्द","विफल","सिस्टम","हल्का","गहरा","उच्च कंट्रास्ट","चयनित","दृश्यमान","सभी स्कैन किए गए","कॉपी","स्थानांतरित","कोई भी","चित्र","वीडियो","शांत","संतुलित","तेज़"],
    "pl": ["H.264 MP4 (zgodny)","H.265 MP4 (mniejszy)","AV1 MKV (najmniejszy)","Proxy H.264 720p","Remuksuj do MKV (bez ponownego kodowania)","Zachowaj rozdzielczość źródłową","Automatycznie (zalecane)","Programowo / CPU","Gotowe","Pominięto","Nieznana rozdzielczość","Konwertowanie","Powodzenie","Anulowano","Niepowodzenie","Systemowy","Jasny","Ciemny","Wysoki kontrast","Wybrane","Widoczne","Wszystkie przeskanowane","Kopiuj","Przenieś","Dowolne","Obrazy","Filmy","Cichy","Zrównoważony","Szybki"],
}

ORDERED_SPECIAL = [key for key in EN if not key.startswith("convert.resolution_10") and key != "convert.resolution_720p"]

for path in sorted(ROOT.glob("*.json")):
    code = path.stem
    pack = json.loads(path.read_text(encoding="utf-8"))
    values = dict(EN)
    if code in OVERRIDES:
        translated = OVERRIDES[code]
        if len(translated) != len(ORDERED_SPECIAL):
            raise RuntimeError(f"{code}: expected {len(ORDERED_SPECIAL)} translations, got {len(translated)}")
        values.update(dict(zip(ORDERED_SPECIAL, translated)))
    pack["strings"].update(values)
    path.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

