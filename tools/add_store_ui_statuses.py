"""Add two missing conversion statuses only; preserve all existing Help/UI copy."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
# Each pair is: duplicate output filename; same as source file.
TEXT={
 'en':('Duplicate output','Same as source'),
 'zh-CN':('输出文件名重复','与源文件相同'),
 'nl':('Dubbele uitvoernaam','Gelijk aan bronbestand'),
 'fr':('Nom de sortie en double','Identique au fichier source'),
 'de':('Doppelter Ausgabename','Identisch mit der Quelldatei'),
 'ja':('出力ファイル名が重複','元のファイルと同じ'),
 'ko':('출력 파일 이름 중복','원본 파일과 동일'),
 'ru':('Повторяющееся имя выходного файла','Совпадает с исходным файлом'),
 'es':('Nombre de salida duplicado','Igual que el archivo de origen'),
 'sv':('Dubblerat utdatafilnamn','Samma som källfilen'),
 'bg':('Дублирано име на изходен файл','Същият като изходния файл'),
 'th':('ชื่อไฟล์ปลายทางซ้ำ','เหมือนกับไฟล์ต้นฉบับ'),
 'id':('Nama berkas keluaran duplikat','Sama dengan berkas sumber'),
 'el':('Διπλό όνομα αρχείου εξόδου','Ίδιο με το αρχείο προέλευσης'),
 'fil':('Magkaparehong pangalan ng output','Kapareho ng pinagmulang file'),
 'hi':('आउटपुट फ़ाइल का नाम दोहराया गया','स्रोत फ़ाइल के समान'),
 'pl':('Powielona nazwa pliku wynikowego','Taki sam jak plik źródłowy'),
 'it':('Nome di output duplicato','Uguale al file sorgente'),
 'ar':('اسم إخراج مكرر','نفس الملف المصدر'),
 'vi':('Tên tệp đầu ra bị trùng','Trùng với tệp nguồn'),
 'uk':('Повторюване ім’я вихідного файлу','Збігається з вихідним файлом'),
 'no':('Duplisert utdatafilnavn','Samme som kildefilen'),
 'fi':('Sama tulostiedoston nimi','Sama kuin lähdetiedosto'),
 'da':('Dubleret outputfilnavn','Samme som kildefilen'),
 'hu':('Ismétlődő kimeneti fájlnév','Azonos a forrásfájllal'),
 'ro':('Nume de ieșire duplicat','Identic cu fișierul sursă'),
 'cs':('Duplicitní název výstupu','Shodné se zdrojovým souborem'),
 'pt-PT':('Nome de saída duplicado','Igual ao ficheiro de origem'),
 'pt-BR':('Nome de saída duplicado','Igual ao arquivo de origem'),
 'tr':('Yinelenen çıktı dosyası adı','Kaynak dosyayla aynı'),
 'zh-TW':('輸出檔名重複','與來源檔案相同'),
 'ms':('Nama fail output pendua','Sama dengan fail sumber'),
 'he':('שם קובץ פלט כפול','זהה לקובץ המקור'),
 'bn':('আউটপুট ফাইলের নাম সদৃশ','উৎস ফাইলের মতোই'),
 'ur':('آؤٹ پٹ فائل کا نام مکرر ہے','ماخذ فائل جیسا'),
 'fa':('نام فایل خروجی تکراری','یکسان با فایل مبدأ'),
 'sk':('Duplicitný názov výstupu','Zhodné so zdrojovým súborom'),
 'hr':('Duplicirani naziv izlazne datoteke','Jednako izvornoj datoteci'),
 'sr':('Дупли назив излазне датотеке','Исто као изворна датотека'),
 'ca':('Nom de sortida duplicat','Igual que el fitxer d’origen'),
 'et':('Korduv väljundfaili nimi','Sama mis lähtefail'),
 'lv':('Dublēts izvades faila nosaukums','Tāds pats kā avota fails'),
 'lt':('Pasikartojantis išvesties failo vardas','Sutampa su šaltinio failu'),
}

def main():
 from localization import SUPPORTED_LANGUAGES
 assert set(TEXT)==set(SUPPORTED_LANGUAGES)
 for code,(duplicate,same) in TEXT.items():
  path=ROOT/'locales'/f'{code}.json'
  pack=json.loads(path.read_text(encoding='utf-8'))
  original_help=json.dumps(pack.get('help'),ensure_ascii=False,sort_keys=True)
  pack['strings']['convert.status_duplicate_output']=duplicate
  pack['strings']['convert.status_same_source']=same
  assert json.dumps(pack.get('help'),ensure_ascii=False,sort_keys=True)==original_help
  path.write_text(json.dumps(pack,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Added two status keys to 43 locales; Help content unchanged.')

if __name__=='__main__':
 import sys
 sys.path.insert(0,str(ROOT))
 main()
