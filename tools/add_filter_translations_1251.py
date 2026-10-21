import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "locales"

KEYS = [
    "title", "orientation", "codec", "tag", "min_rating", "color",
    "min_width", "max_width", "min_height", "max_height", "min_size", "max_size",
    "min_duration", "max_duration", "date_from", "date_to", "any", "landscape",
    "portrait", "square", "unlabelled", "clear", "apply",
]

T = {
"en": ["Advanced filters","Orientation","Codec contains","Tag contains","Minimum rating","Colour label","Minimum width (pixels)","Maximum width (pixels)","Minimum height (pixels)","Maximum height (pixels)","Minimum size (MB)","Maximum size (MB)","Minimum duration (seconds)","Maximum duration (seconds)","Modified from (YYYY-MM-DD)","Modified to (YYYY-MM-DD)","Any","Landscape","Portrait","Square","Unlabelled","Clear","Apply"],
"zh-CN": ["高级筛选","方向","编解码器包含","标签包含","最低评分","颜色标签","最小宽度（像素）","最大宽度（像素）","最小高度（像素）","最大高度（像素）","最小大小（MB）","最大大小（MB）","最短时长（秒）","最长时长（秒）","修改日期起（YYYY-MM-DD）","修改日期止（YYYY-MM-DD）","任意","横向","纵向","正方形","无标签","清除","应用"],
"nl": ["Geavanceerde filters","Oriëntatie","Codec bevat","Tag bevat","Minimale beoordeling","Kleurlabel","Minimale breedte (pixels)","Maximale breedte (pixels)","Minimale hoogte (pixels)","Maximale hoogte (pixels)","Minimale grootte (MB)","Maximale grootte (MB)","Minimale duur (seconden)","Maximale duur (seconden)","Gewijzigd vanaf (JJJJ-MM-DD)","Gewijzigd tot (JJJJ-MM-DD)","Alle","Liggend","Staand","Vierkant","Zonder label","Wissen","Toepassen"],
"fr": ["Filtres avancés","Orientation","Le codec contient","L’étiquette contient","Note minimale","Étiquette de couleur","Largeur minimale (pixels)","Largeur maximale (pixels)","Hauteur minimale (pixels)","Hauteur maximale (pixels)","Taille minimale (Mo)","Taille maximale (Mo)","Durée minimale (secondes)","Durée maximale (secondes)","Modifié à partir du (AAAA-MM-JJ)","Modifié jusqu’au (AAAA-MM-JJ)","Tous","Paysage","Portrait","Carré","Sans étiquette","Effacer","Appliquer"],
"de": ["Erweiterte Filter","Ausrichtung","Codec enthält","Tag enthält","Mindestbewertung","Farblabel","Mindestbreite (Pixel)","Maximalbreite (Pixel)","Mindesthöhe (Pixel)","Maximalhöhe (Pixel)","Mindestgröße (MB)","Maximalgröße (MB)","Mindestdauer (Sekunden)","Maximaldauer (Sekunden)","Geändert ab (JJJJ-MM-TT)","Geändert bis (JJJJ-MM-TT)","Alle","Querformat","Hochformat","Quadratisch","Ohne Label","Leeren","Anwenden"],
"ja": ["詳細フィルター","向き","コーデックに含む","タグに含む","最低評価","カラーラベル","最小幅（ピクセル）","最大幅（ピクセル）","最小高さ（ピクセル）","最大高さ（ピクセル）","最小サイズ（MB）","最大サイズ（MB）","最短時間（秒）","最長時間（秒）","更新日（開始、YYYY-MM-DD）","更新日（終了、YYYY-MM-DD）","すべて","横向き","縦向き","正方形","ラベルなし","クリア","適用"],
"ko": ["고급 필터","방향","코덱 포함","태그 포함","최소 평점","색상 레이블","최소 너비(픽셀)","최대 너비(픽셀)","최소 높이(픽셀)","최대 높이(픽셀)","최소 크기(MB)","최대 크기(MB)","최소 길이(초)","최대 길이(초)","수정 시작일(YYYY-MM-DD)","수정 종료일(YYYY-MM-DD)","모두","가로","세로","정사각형","레이블 없음","지우기","적용"],
"ru": ["Расширенные фильтры","Ориентация","Кодек содержит","Тег содержит","Минимальный рейтинг","Цветовая метка","Минимальная ширина (пиксели)","Максимальная ширина (пиксели)","Минимальная высота (пиксели)","Максимальная высота (пиксели)","Минимальный размер (МБ)","Максимальный размер (МБ)","Минимальная длительность (секунды)","Максимальная длительность (секунды)","Изменено с (ГГГГ-ММ-ДД)","Изменено до (ГГГГ-ММ-ДД)","Любой","Альбомная","Портретная","Квадратная","Без метки","Очистить","Применить"],
"es": ["Filtros avanzados","Orientación","El códec contiene","La etiqueta contiene","Valoración mínima","Etiqueta de color","Anchura mínima (píxeles)","Anchura máxima (píxeles)","Altura mínima (píxeles)","Altura máxima (píxeles)","Tamaño mínimo (MB)","Tamaño máximo (MB)","Duración mínima (segundos)","Duración máxima (segundos)","Modificado desde (AAAA-MM-DD)","Modificado hasta (AAAA-MM-DD)","Cualquiera","Horizontal","Vertical","Cuadrado","Sin etiqueta","Borrar","Aplicar"],
"sv": ["Avancerade filter","Orientering","Kodeken innehåller","Taggen innehåller","Lägsta betyg","Färgetikett","Minsta bredd (pixlar)","Största bredd (pixlar)","Minsta höjd (pixlar)","Största höjd (pixlar)","Minsta storlek (MB)","Största storlek (MB)","Kortaste längd (sekunder)","Längsta längd (sekunder)","Ändrad från (ÅÅÅÅ-MM-DD)","Ändrad till (ÅÅÅÅ-MM-DD)","Alla","Liggande","Stående","Kvadratisk","Utan etikett","Rensa","Tillämpa"],
"bg": ["Разширени филтри","Ориентация","Кодекът съдържа","Етикетът съдържа","Минимална оценка","Цветен етикет","Минимална ширина (пиксели)","Максимална ширина (пиксели)","Минимална височина (пиксели)","Максимална височина (пиксели)","Минимален размер (MB)","Максимален размер (MB)","Минимална продължителност (секунди)","Максимална продължителност (секунди)","Променено от (ГГГГ-ММ-ДД)","Променено до (ГГГГ-ММ-ДД)","Всички","Хоризонтална","Вертикална","Квадратна","Без етикет","Изчисти","Приложи"],
"th": ["ตัวกรองขั้นสูง","แนวภาพ","ตัวแปลงสัญญาณมีคำว่า","แท็กมีคำว่า","คะแนนขั้นต่ำ","ป้ายสี","ความกว้างขั้นต่ำ (พิกเซล)","ความกว้างสูงสุด (พิกเซล)","ความสูงขั้นต่ำ (พิกเซล)","ความสูงสูงสุด (พิกเซล)","ขนาดขั้นต่ำ (MB)","ขนาดสูงสุด (MB)","ระยะเวลาขั้นต่ำ (วินาที)","ระยะเวลาสูงสุด (วินาที)","แก้ไขตั้งแต่ (YYYY-MM-DD)","แก้ไขถึง (YYYY-MM-DD)","ทั้งหมด","แนวนอน","แนวตั้ง","จัตุรัส","ไม่มีป้าย","ล้าง","นำไปใช้"],
"id": ["Filter lanjutan","Orientasi","Codec berisi","Tag berisi","Peringkat minimum","Label warna","Lebar minimum (piksel)","Lebar maksimum (piksel)","Tinggi minimum (piksel)","Tinggi maksimum (piksel)","Ukuran minimum (MB)","Ukuran maksimum (MB)","Durasi minimum (detik)","Durasi maksimum (detik)","Diubah mulai (YYYY-MM-DD)","Diubah hingga (YYYY-MM-DD)","Apa saja","Lanskap","Potret","Persegi","Tanpa label","Hapus","Terapkan"],
"el": ["Σύνθετα φίλτρα","Προσανατολισμός","Ο κωδικοποιητής περιέχει","Η ετικέτα περιέχει","Ελάχιστη βαθμολογία","Έγχρωμη ετικέτα","Ελάχιστο πλάτος (pixel)","Μέγιστο πλάτος (pixel)","Ελάχιστο ύψος (pixel)","Μέγιστο ύψος (pixel)","Ελάχιστο μέγεθος (MB)","Μέγιστο μέγεθος (MB)","Ελάχιστη διάρκεια (δευτερόλεπτα)","Μέγιστη διάρκεια (δευτερόλεπτα)","Τροποποιήθηκε από (ΕΕΕΕ-ΜΜ-ΗΗ)","Τροποποιήθηκε έως (ΕΕΕΕ-ΜΜ-ΗΗ)","Οποιοδήποτε","Οριζόντιο","Κατακόρυφο","Τετράγωνο","Χωρίς ετικέτα","Εκκαθάριση","Εφαρμογή"],
"fil": ["Mga advanced na filter","Oryentasyon","May ganitong codec","May ganitong tag","Pinakamababang rating","Kulay na label","Pinakamababang lapad (pixel)","Pinakamalaking lapad (pixel)","Pinakamababang taas (pixel)","Pinakamalaking taas (pixel)","Pinakamababang laki (MB)","Pinakamalaking laki (MB)","Pinakamaikling haba (segundo)","Pinakamahabang haba (segundo)","Binago mula (YYYY-MM-DD)","Binago hanggang (YYYY-MM-DD)","Anuman","Pahalang","Patayo","Parisukat","Walang label","I-clear","Ilapat"],
"hi": ["उन्नत फ़िल्टर","दिशा","कोडेक में शामिल","टैग में शामिल","न्यूनतम रेटिंग","रंग लेबल","न्यूनतम चौड़ाई (पिक्सेल)","अधिकतम चौड़ाई (पिक्सेल)","न्यूनतम ऊँचाई (पिक्सेल)","अधिकतम ऊँचाई (पिक्सेल)","न्यूनतम आकार (MB)","अधिकतम आकार (MB)","न्यूनतम अवधि (सेकंड)","अधिकतम अवधि (सेकंड)","इस तारीख से संशोधित (YYYY-MM-DD)","इस तारीख तक संशोधित (YYYY-MM-DD)","कोई भी","लैंडस्केप","पोर्ट्रेट","वर्गाकार","बिना लेबल","साफ़ करें","लागू करें"],
"pl": ["Filtry zaawansowane","Orientacja","Kodek zawiera","Tag zawiera","Minimalna ocena","Etykieta koloru","Minimalna szerokość (piksele)","Maksymalna szerokość (piksele)","Minimalna wysokość (piksele)","Maksymalna wysokość (piksele)","Minimalny rozmiar (MB)","Maksymalny rozmiar (MB)","Minimalny czas (sekundy)","Maksymalny czas (sekundy)","Zmodyfikowano od (RRRR-MM-DD)","Zmodyfikowano do (RRRR-MM-DD)","Dowolne","Pozioma","Pionowa","Kwadratowa","Bez etykiety","Wyczyść","Zastosuj"],
}

for code, values in T.items():
    path = ROOT / f"{code}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    for key, value in zip(KEYS, values, strict=True):
        data["strings"][f"filters.{key}"] = value
    for rating in range(1, 6):
        data["strings"][f"filters.rating_{rating}"] = str(rating)
    if code == "es":
        data["strings"]["inspector.title"] = "Inspector"
        data["strings"]["inspector.open"] = "Abrir"
    if code == "fil":
        data["strings"]["pane.preview"] = "Paunang tingin"
        data["strings"]["pane.live"] = "Agarang update"
        data["strings"]["preview.play"] = "I-play"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
