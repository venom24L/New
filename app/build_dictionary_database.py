#!/usr/bin/env python3
import os
import re
import sys
import gzip
import io
import urllib.request
import sqlite3

def clean_text(t):
    if not t:
        return ""
    t = re.sub(r'\[.*?\]', '', t)
    t = re.sub(r'\(.*?\)', '', t)
    t = re.sub(r'<.*?>', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def main():
    db_dir = "app/src/main/assets/databases"
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "deutschar.db")
    
    if os.path.exists(db_path):
        os.remove(db_path)

    print("Connecting to SQLite database at:", db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Create tables
    cur.execute("""CREATE TABLE IF NOT EXISTS `words` (
        `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        `germanWord` TEXT NOT NULL,
        `article` TEXT,
        `plural` TEXT,
        `wordType` TEXT NOT NULL,
        `arabicTranslation` TEXT NOT NULL,
        `level` INTEGER NOT NULL,
        `frequencyRank` INTEGER,
        `originNounId` INTEGER,
        `status` TEXT NOT NULL,
        `pos` TEXT NOT NULL,
        `source` TEXT NOT NULL
    )""")
    cur.execute("CREATE INDEX IF NOT EXISTS `index_words_germanWord` ON `words` (`germanWord`)")
    cur.execute("CREATE INDEX IF NOT EXISTS `index_words_arabicTranslation` ON `words` (`arabicTranslation`)")
    cur.execute("CREATE INDEX IF NOT EXISTS `index_words_plural` ON `words` (`plural`)")

    cur.execute("""CREATE TABLE IF NOT EXISTS `german_nouns` (
        `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        `lemma` TEXT NOT NULL,
        `article` TEXT,
        `genus` TEXT,
        `pos` TEXT,
        `nominativSingular` TEXT,
        `nominativPlural` TEXT,
        `genitivSingular` TEXT,
        `genitivPlural` TEXT,
        `dativSingular` TEXT,
        `dativPlural` TEXT,
        `akkusativSingular` TEXT,
        `akkusativPlural` TEXT,
        `rawGrammar` TEXT,
        `flexion` TEXT
    )""")
    cur.execute("CREATE INDEX IF NOT EXISTS `index_german_nouns_lemma` ON `german_nouns` (`lemma`)")
    cur.execute("CREATE INDEX IF NOT EXISTS `index_german_nouns_nominativPlural` ON `german_nouns` (`nominativPlural`)")

    cur.execute("""CREATE TABLE IF NOT EXISTS `german_verbs` (
        `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        `infinitive` TEXT NOT NULL,
        `auxiliary` TEXT NOT NULL,
        `presentIch` TEXT,
        `presentDu` TEXT,
        `presentErSieEs` TEXT,
        `presentWir` TEXT,
        `presentIhr` TEXT,
        `presentSie` TEXT,
        `pastIch` TEXT,
        `pastDu` TEXT,
        `pastErSieEs` TEXT,
        `pastWir` TEXT,
        `pastIhr` TEXT,
        `pastSie` TEXT,
        `partizipZwei` TEXT,
        `konjunktivZwei` TEXT,
        `imperativSingularForm` TEXT,
        `imperativPluralForm` TEXT,
        `isSeparable` INTEGER NOT NULL,
        `prefix` TEXT
    )""")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS `index_german_verbs_infinitive` ON `german_verbs` (`infinitive`)")

    cur.execute("""CREATE TABLE IF NOT EXISTS `examples` (
        `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        `wordId` INTEGER NOT NULL,
        `germanSentence` TEXT NOT NULL,
        `arabicTranslation` TEXT NOT NULL
    )""")
    cur.execute("CREATE INDEX IF NOT EXISTS `index_examples_wordId` ON `examples` (`wordId`)")

    cur.execute("""CREATE TABLE IF NOT EXISTS `history` (
        `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        `word_id` INTEGER,
        `query` TEXT NOT NULL,
        `source_language` TEXT NOT NULL,
        `target_language` TEXT NOT NULL,
        `result_type` TEXT NOT NULL,
        `result_text` TEXT NOT NULL,
        `is_saved` INTEGER NOT NULL,
        `searched_at` INTEGER NOT NULL,
        FOREIGN KEY(`word_id`) REFERENCES `words`(`id`) ON UPDATE NO ACTION ON DELETE SET NULL
    )""")
    cur.execute("CREATE INDEX IF NOT EXISTS `index_history_searched_at` ON `history` (`searched_at`)")
    cur.execute("CREATE INDEX IF NOT EXISTS `index_history_word_id` ON `history` (`word_id`)")
    cur.execute("CREATE INDEX IF NOT EXISTS `index_history_query` ON `history` (`query`)")

    cur.execute("""CREATE TABLE IF NOT EXISTS `cheatsheet_items` (
        `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        `phrase` TEXT NOT NULL,
        `translation` TEXT NOT NULL,
        `category` TEXT NOT NULL,
        `languagePair` TEXT NOT NULL,
        `notes` TEXT NOT NULL,
        `createdAt` INTEGER NOT NULL
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS `conjugations` (
        `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        `word_id` INTEGER NOT NULL,
        `tense` TEXT NOT NULL,
        `person` TEXT NOT NULL,
        `form` TEXT NOT NULL,
        `source` TEXT NOT NULL,
        FOREIGN KEY(`word_id`) REFERENCES `words`(`id`) ON UPDATE NO ACTION ON DELETE CASCADE
    )""")
    cur.execute("CREATE INDEX IF NOT EXISTS `index_conjugations_word_id` ON `conjugations` (`word_id`)")
    cur.execute("CREATE INDEX IF NOT EXISTS `index_conjugations_form` ON `conjugations` (`form`)")

    cur.execute("CREATE TABLE IF NOT EXISTS room_master_table (id INTEGER PRIMARY KEY,identity_hash TEXT)")
    cur.execute("INSERT OR REPLACE INTO room_master_table (id,identity_hash) VALUES(42, '7ceea1d5c8fe8fbd395db8641dcc5701')")

    conn.commit()

    print("Tables created successfully. Now fetching datasets...")
    
    # 1. Fetch Ding dictionary
    print("Downloading TU Chemnitz German-English dictionary (de-en.txt.gz)...")
    req_ding = urllib.request.Request("https://ftp.tu-chemnitz.de/pub/Local/urz/ding/de-en/de-en.txt.gz", headers={"User-Agent": "Mozilla/5.0"})
    raw_gz = urllib.request.urlopen(req_ding, timeout=40).read()
    ding_text = gzip.GzipFile(fileobj=io.BytesIO(raw_gz)).read().decode("utf-8", errors="ignore")

    # 2. Fetch frequency ranking list
    print("Downloading German frequency list...")
    req_freq = urllib.request.Request("https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/de/de_full.txt", headers={"User-Agent": "Mozilla/5.0"})
    freq_text = urllib.request.urlopen(req_freq, timeout=30).read().decode("utf-8", errors="ignore")
    
    freq_map = {}
    rank = 1
    for line in freq_text.splitlines():
        line = line.strip()
        if not line:
            continue
        p = line.split()
        w = p[0]
        if w not in freq_map:
            freq_map[w] = rank
            rank += 1
            if rank > 200000:
                break
    print(f"Loaded {len(freq_map)} frequency rankings.")

    # Process Ding dictionary
    print("Processing dictionary entries...")
    words_map = {} # germanWord -> dict

    for line in ding_text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split(' :: ')
        if len(parts) != 2:
            continue
        de_side, en_side = parts[0].strip(), parts[1].strip()
        
        de_parts = de_side.split(' | ')
        base_de = de_parts[0]
        plural_candidate = de_parts[1] if len(de_parts) > 1 else None
        
        plural_word = None
        if plural_candidate and '{pl}' in plural_candidate:
            pl_cleaned = clean_text(plural_candidate.replace('{pl}', '').split(';')[0])
            if pl_cleaned and len(pl_cleaned) < 50:
                plural_word = pl_cleaned

        sub_entries = base_de.split(';')
        for sub in sub_entries:
            sub = sub.strip()
            if not sub:
                continue
            
            article = None
            word_type = 'noun'
            
            if '{m}' in sub:
                article = 'der'
                word_type = 'noun'
            elif '{f}' in sub:
                article = 'die'
                word_type = 'noun'
            elif '{n}' in sub:
                article = 'das'
                word_type = 'noun'
            elif '{pl}' in sub:
                article = 'die'
                word_type = 'noun'
            elif any(x in sub for x in ['{vi}', '{vt}', '{vr}', '{v}']):
                word_type = 'verb'
            elif '{adj}' in sub:
                word_type = 'adjective'
            elif '{adv}' in sub:
                word_type = 'adverb'
            elif '{prep}' in sub:
                word_type = 'preposition'
            elif '{conj}' in sub:
                word_type = 'conjunction'
            elif '{pron}' in sub:
                word_type = 'pronoun'
            else:
                if sub.endswith('en') and sub[0].islower() and ' ' not in sub:
                    word_type = 'verb'
                elif sub[0].isupper() and ' ' not in sub:
                    word_type = 'noun'
                else:
                    word_type = 'phrase' if ' ' in sub else 'other'

            raw_word = re.sub(r'\{.*?\}', '', sub)
            cleaned_word = clean_text(raw_word)
            if not cleaned_word or len(cleaned_word) > 70 or cleaned_word.startswith('-') or cleaned_word.endswith('-'):
                continue
            
            cleaned_en = clean_text(en_side.split(' | ')[0].split(';')[0])
            if not cleaned_en:
                cleaned_en = cleaned_word

            # Calculate frequency and CEFR level estimate
            fr = freq_map.get(cleaned_word) or freq_map.get(cleaned_word.lower())
            level = 0
            if fr:
                if fr <= 1000:
                    level = 1 # A1
                elif fr <= 3000:
                    level = 2 # A2
                elif fr <= 7000:
                    level = 3 # B1
                elif fr <= 15000:
                    level = 4 # B2
                else:
                    level = 5 # C1
            
            if cleaned_word not in words_map:
                words_map[cleaned_word] = {
                    'germanWord': cleaned_word,
                    'article': article,
                    'plural': plural_word,
                    'wordType': word_type,
                    'arabicTranslation': cleaned_en, # English/Arabic gloss
                    'level': level,
                    'frequencyRank': fr,
                    'originNounId': None,
                    'status': 'ACTIVE',
                    'pos': word_type,
                    'source': 'ding_chemnitz'
                }
            else:
                # Merge if missing article or plural
                if not words_map[cleaned_word]['article'] and article:
                    words_map[cleaned_word]['article'] = article
                if not words_map[cleaned_word]['plural'] and plural_word:
                    words_map[cleaned_word]['plural'] = plural_word

    print(f"Total processed words from Ding: {len(words_map)}")

    # Add remaining top frequency words if not present
    print("Augmenting with high-frequency German wordlist...")
    added_freq = 0
    for w, r in freq_map.items():
        if w not in words_map and len(w) >= 2 and re.match(r'^[a-zA-ZäöüÄÖÜß\-\.]+$', w):
            w_type = "noun" if w[0].isupper() else ("verb" if w.endswith("en") else "other")
            lvl = 1 if r <= 1000 else (2 if r <= 3000 else (3 if r <= 7000 else (4 if r <= 15000 else 5)))
            words_map[w] = {
                'germanWord': w,
                'article': 'die' if w_type == 'noun' and w.endswith(('ung', 'heit', 'keit', 'schaft', 'ion')) else ('der' if w_type == 'noun' and w.endswith(('er', 'ismus', 'ling')) else ('das' if w_type == 'noun' and w.endswith(('chen', 'lein', 'ment', 'um')) else None)),
                'plural': None,
                'wordType': w_type,
                'arabicTranslation': w,
                'level': lvl,
                'frequencyRank': r,
                'originNounId': None,
                'status': 'ACTIVE',
                'pos': w_type,
                'source': 'frequency_lexicon'
            }
            added_freq += 1

    print(f"Total vocabulary words ready for database: {len(words_map)} (Augmented with {added_freq} freq words)")

    # Sort words so top frequency / shorter words come first
    sorted_words = sorted(
        words_map.values(),
        key=lambda x: (x['frequencyRank'] if x['frequencyRank'] is not None else 999999, len(x['germanWord']))
    )

    # Insert into words table in batches
    print("Inserting words into SQLite database...")
    insert_word_sql = """INSERT INTO words 
        (germanWord, article, plural, wordType, arabicTranslation, level, frequencyRank, originNounId, status, pos, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    
    batch_size = 5000
    batch = []
    word_id_counter = 1
    
    for item in sorted_words:
        batch.append((
            item['germanWord'],
            item['article'],
            item['plural'],
            item['wordType'],
            item['arabicTranslation'],
            item['level'],
            item['frequencyRank'],
            item['originNounId'],
            item['status'],
            item['pos'],
            item['source']
        ))
        if len(batch) >= batch_size:
            cur.executemany(insert_word_sql, batch)
            conn.commit()
            batch = []
            print(f"Inserted {word_id_counter * batch_size} words...")
            word_id_counter += 1

    if batch:
        cur.executemany(insert_word_sql, batch)
        conn.commit()

    total_words_inserted = cur.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    print(f"Successfully inserted {total_words_inserted} words into 'words' table!")

    # Populate german_verbs table for common verbs
    print("Populating german_verbs and conjugations...")
    verbs_data = [
        ("sein", "sein", "bin", "bist", "ist", "sind", "seid", "sind", "war", "warst", "war", "waren", "wart", "waren", "gewesen", "wäre", "sei", "seid", 0, None),
        ("haben", "haben", "habe", "hast", "hat", "haben", "habt", "haben", "hatte", "hattest", "hatte", "hatten", "hattet", "hatten", "gehabt", "hätte", "habe", "habt", 0, None),
        ("werden", "sein", "werde", "wirst", "wird", "werden", "werdet", "werden", "wurde", "wurdest", "wurde", "wurden", "wurdet", "wurden", "geworden", "würde", "werde", "werdet", 0, None),
        ("können", "haben", "kann", "kannst", "kann", "können", "könnt", "können", "konnte", "konntest", "konnte", "konnten", "konntet", "konnten", "gekonnt", "könnte", "kann", "könnt", 0, None),
        ("müssen", "haben", "muss", "musst", "muss", "müssen", "müsst", "müssen", "musste", "musstest", "musste", "mussten", "musstet", "mussten", "gemusst", "müsste", "muss", "müsst", 0, None),
        ("wollen", "haben", "will", "willst", "will", "wollen", "wollt", "wollen", "wollte", "wolltest", "wollte", "wollten", "wolltet", "wollten", "gewollt", "wollte", "wolle", "wollt", 0, None),
        ("sollen", "haben", "soll", "sollst", "soll", "sollen", "sollt", "sollen", "sollte", "solltest", "sollte", "sollten", "solltet", "sollten", "gesollt", "sollte", "solle", "sollt", 0, None),
        ("dürfen", "haben", "darf", "darfst", "darf", "dürfen", "dürft", "dürfen", "durfte", "durftest", "durfte", "durften", "durftet", "durften", "gedurft", "dürfte", "darf", "dürft", 0, None),
        ("mögen", "haben", "mag", "magst", "mag", "mögen", "mögt", "mögen", "mochte", "mochtest", "mochte", "mochten", "mochtet", "mochten", "gemocht", "möchte", "mag", "mög", 0, None),
        ("gehen", "sein", "gehe", "gehst", "geht", "gehen", "geht", "gehen", "ging", "gingst", "ging", "gingen", "gingt", "gingen", "gegangen", "ginge", "geh", "geht", 0, None),
        ("kommen", "sein", "komme", "kommst", "kommt", "kommen", "kommt", "kommen", "kam", "kamst", "kam", "kamen", "kamt", "kamen", "gekommen", "käme", "komm", "kommt", 0, None),
        ("machen", "haben", "mache", "machst", "macht", "machen", "macht", "machen", "machte", "machtest", "machte", "machten", "machtet", "machten", "gemacht", "machte", "mach", "macht", 0, None),
        ("sagen", "haben", "sage", "sagst", "sagt", "sagen", "sagt", "sagen", "sagte", "sagtest", "sagte", "sagten", "sagtet", "sagten", "gesagt", "sagte", "sag", "sagt", 0, None),
        ("geben", "haben", "gebe", "gibst", "gibt", "geben", "gebt", "geben", "gab", "gabst", "gab", "gaben", "gabt", "gaben", "gegeben", "gäbe", "gib", "gebt", 0, None),
        ("sehen", "haben", "sehe", "siehst", "sieht", "sehen", "seht", "sehen", "sah", "sahst", "sah", "sahen", "saht", "sahen", "gesehen", "sähe", "sieh", "seht", 0, None),
        ("lassen", "haben", "lasse", "lässt", "lässt", "lassen", "lasst", "lassen", "ließ", "ließest", "ließ", "ließen", "ließt", "ließen", "gelassen", "ließe", "lass", "lasst", 0, None),
        ("stehen", "haben", "stehe", "stehst", "steht", "stehen", "steht", "stehen", "stand", "standest", "stand", "standen", "standet", "standen", "gestanden", "stünde", "steh", "steht", 0, None),
        ("finden", "haben", "finde", "findest", "findet", "finden", "findet", "finden", "fand", "fandest", "fand", "fanden", "fandet", "fanden", "gefunden", "fände", "finde", "findet", 0, None),
        ("bleiben", "sein", "bleibe", "bleibst", "bleibt", "bleiben", "bleibt", "bleiben", "blieb", "bliebst", "blieb", "blieben", "bliebt", "blieben", "geblieben", "bliebe", "bleib", "bleibt", 0, None),
        ("liegen", "haben", "liege", "liegst", "liegt", "liegen", "liegt", "liegen", "lag", "lagst", "lag", "lagen", "lagt", "lagen", "gelegen", "läge", "lieg", "liegt", 0, None),
        ("heißen", "haben", "heiße", "heißt", "heißt", "heißen", "heißt", "heißen", "hieß", "hießest", "hieß", "hießen", "hießt", "hießen", "geheißen", "hieße", "heiß", "heißt", 0, None),
        ("denken", "haben", "denke", "denkst", "denkt", "denken", "denkt", "denken", "dachte", "dachtest", "dachte", "dachten", "dachtet", "dachten", "gedacht", "dächte", "denk", "denkt", 0, None),
        ("nehmen", "haben", "nehme", "nimmst", "nimmt", "nehmen", "nehmt", "nehmen", "nahm", "nahmst", "nahm", "nahmen", "nahmt", "nahmen", "genommen", "nähme", "nimm", "nehmt", 0, None),
        ("tun", "haben", "tue", "tust", "tut", "tun", "tut", "tun", "tat", "tatest", "tat", "taten", "tatet", "taten", "getan", "täte", "tu", "tut", 0, None),
        ("glauben", "haben", "glaube", "glaubst", "glaubt", "glauben", "glaubt", "glauben", "glaubte", "glaubtest", "glaubte", "glaubten", "glaubtet", "glaubten", "geglaubt", "glaubte", "glaub", "glaubt", 0, None),
        ("halten", "haben", "halte", "hältst", "hält", "halten", "haltet", "halten", "hielt", "hieltest", "hielt", "hielten", "hieltet", "hielten", "gehalten", "hielte", "halt", "haltet", 0, None),
        ("nennen", "haben", "nenne", "nennst", "nennt", "nennen", "nennt", "nennen", "nannte", "nanntest", "nannte", "nannten", "nanntet", "nannten", "genannt", "nennte", "nenn", "nennt", 0, None),
        ("sprechen", "haben", "spreche", "sprichst", "spricht", "sprechen", "sprecht", "sprechen", "sprach", "sprachst", "sprach", "sprachen", "spracht", "sprachen", "gesprochen", "spräche", "sprich", "sprecht", 0, None),
        ("bringen", "haben", "bringe", "bringst", "bringt", "bringen", "bringt", "bringen", "brachte", "brachtest", "brachte", "brachten", "brachtet", "brachten", "gebracht", "brächte", "bring", "bringt", 0, None),
        ("leben", "haben", "lebe", "lebst", "lebt", "leben", "lebt", "leben", "lebte", "lebtest", "lebte", "lebten", "lebtet", "lebten", "gelebt", "lebte", "leb", "lebt", 0, None),
        ("fahren", "sein", "fahre", "fährst", "fährt", "fahren", "fahrt", "fahren", "fuhr", "fuhrst", "fuhr", "fuhren", "fuhrt", "fuhren", "gefahren", "führe", "fahr", "fahrt", 0, None),
        ("arbeiten", "haben", "arbeite", "arbeitest", "arbeitet", "arbeiten", "arbeitet", "arbeiten", "arbeitete", "arbeitetest", "arbeitete", "arbeiteten", "arbeitetet", "arbeiteten", "gearbeitet", "arbeitete", "arbeite", "arbeitet", 0, None),
        ("brauchen", "haben", "brauche", "brauchst", "braucht", "brauchen", "braucht", "brauchen", "brauchte", "brauchtest", "brauchte", "brauchten", "brauchtet", "brauchten", "gebraucht", "brauchte", "brauch", "braucht", 0, None),
        ("folgen", "sein", "folge", "folgst", "folgt", "folgen", "folgt", "folgen", "folgte", "folgtest", "folgte", "folgten", "folgtet", "folgten", "gefolgt", "folgte", "folg", "folgt", 0, None),
        ("lernen", "haben", "lerne", "lernst", "lernt", "lernen", "lernt", "lernen", "lernte", "lerntest", "lernte", "lernten", "lerntet", "lernten", "gelernt", "lernte", "lern", "lernt", 0, None),
        ("verstehen", "haben", "verstehe", "verstehst", "versteht", "verstehen", "versteht", "verstehen", "verstand", "verstandest", "verstand", "verstanden", "verstandet", "verstanden", "verstanden", "verstände", "versteh", "versteht", 0, None),
        ("ankommen", "sein", "komme an", "kommst an", "kommt an", "kommen an", "kommt an", "kommen an", "kam an", "kamst an", "kam an", "kamen an", "kamt an", "kamen an", "angekommen", "käme an", "komm an", "kommt an", 1, "an"),
        ("aufstehen", "sein", "stehe auf", "stehst auf", "steht auf", "stehen auf", "steht auf", "stehen auf", "stand auf", "standest auf", "stand auf", "standen auf", "standet auf", "standen auf", "aufgestanden", "stünde auf", "steh auf", "steht auf", 1, "auf"),
        ("einkaufen", "haben", "kaufe ein", "kaufst ein", "kauft ein", "kaufen ein", "kauft ein", "kaufen ein", "kaufte ein", "kauftest ein", "kaufte ein", "kauften ein", "kauftet ein", "kauften ein", "eingekauft", "kaufte ein", "kauf ein", "kauft ein", 1, "ein")
    ]
    cur.executemany("""INSERT INTO german_verbs 
        (infinitive, auxiliary, presentIch, presentDu, presentErSieEs, presentWir, presentIhr, presentSie,
         pastIch, pastDu, pastErSieEs, pastWir, pastIhr, pastSie, partizipZwei, konjunktivZwei,
         imperativSingularForm, imperativPluralForm, isSeparable, prefix)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", verbs_data)

    # Populate sample german_nouns
    nouns_data = [
        ("Haus", "das", "Neutrum", "Substantiv", "das Haus", "die Häuser", "des Hauses", "der Häuser", "dem Haus", "den Häusern", "das Haus", "die Häuser", "n", "{n}"),
        ("Buch", "das", "Neutrum", "Substantiv", "das Buch", "die Bücher", "des Buches", "der Bücher", "dem Buch", "den Büchern", "das Buch", "die Bücher", "n", "{n}"),
        ("Mann", "der", "Maskulinum", "Substantiv", "der Mann", "die Männer", "des Mannes", "der Männer", "dem Mann", "den Männern", "den Mann", "die Männer", "m", "{m}"),
        ("Frau", "die", "Femininum", "Substantiv", "die Frau", "die Frauen", "der Frau", "der Frauen", "der Frau", "den Frauen", "die Frau", "die Frauen", "f", "{f}"),
        ("Kind", "das", "Neutrum", "Substantiv", "das Kind", "die Kinder", "des Kindes", "der Kinder", "dem Kind", "den Kindern", "das Kind", "die Kinder", "n", "{n}"),
        ("Stadt", "die", "Femininum", "Substantiv", "die Stadt", "die Städte", "der Stadt", "der Städte", "der Stadt", "den Städten", "die Stadt", "die Städte", "f", "{f}"),
        ("Tag", "der", "Maskulinum", "Substantiv", "der Tag", "die Tage", "des Tages", "der Tage", "dem Tag", "den Tagen", "den Tag", "die Tage", "m", "{m}"),
        ("Jahr", "das", "Neutrum", "Substantiv", "das Jahr", "die Jahre", "des Jahres", "der Jahre", "dem Jahr", "den Jahren", "das Jahr", "die Jahre", "n", "{n}"),
        ("Zeit", "die", "Femininum", "Substantiv", "die Zeit", "die Zeiten", "der Zeit", "der Zeiten", "der Zeit", "den Zeiten", "die Zeit", "die Zeiten", "f", "{f}"),
        ("Hand", "die", "Femininum", "Substantiv", "die Hand", "die Hände", "der Hand", "der Hände", "der Hand", "den Händen", "die Hand", "die Hände", "f", "{f}"),
        ("Auge", "das", "Neutrum", "Substantiv", "das Auge", "die Augen", "des Auges", "der Augen", "dem Auge", "den Augen", "das Auge", "die Augen", "n", "{n}"),
        ("Weg", "der", "Maskulinum", "Substantiv", "der Weg", "die Wege", "des Weges", "der Wege", "dem Weg", "den Wegen", "den Weg", "die Wege", "m", "{m}"),
        ("Leben", "das", "Neutrum", "Substantiv", "das Leben", "die Leben", "des Lebens", "der Leben", "dem Leben", "den Leben", "das Leben", "die Leben", "n", "{n}")
    ]
    cur.executemany("""INSERT INTO german_nouns 
        (lemma, article, genus, pos, nominativSingular, nominativPlural, genitivSingular, genitivPlural,
         dativSingular, dativPlural, akkusativSingular, akkusativPlural, rawGrammar, flexion)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", nouns_data)

    # Populate cheat sheet items
    cheatsheets = [
        ("Guten Morgen", "صباح الخير", "تحيات", "de-ar", "تقال في الصباح الباكر حتى الظهر"),
        ("Guten Tag", "طاب يومك / مرحباً", "تحيات", "de-ar", "التحية الرسمية الأكثر شيوعاً"),
        ("Guten Abend", "مساء الخير", "تحيات", "de-ar", "تقال من بداية المساء"),
        ("Gute Nacht", "تصبح على خير", "تحيات", "de-ar", "تقال عند النوم حصراً"),
        ("Auf Wiedersehen", "إلى اللقاء (رسمي)", "تحيات", "de-ar", "تستخدم في الوداع الرسمي"),
        ("Tschüss", "مع السلامة / باي", "تحيات", "de-ar", "غير رسمية بين الأصدقاء"),
        ("Wie geht es Ihnen?", "كيف حال حضرتك؟", "أسئلة شائعة", "de-ar", "صيغة الاحترام الرسمية"),
        ("Wie geht's?", "كيف الحال؟", "أسئلة شائعة", "de-ar", "صيغة غير رسمية"),
        ("Danke schön", "شكراً جزيلاً", "مجاملات", "de-ar", "عبارة شكر مهذبة"),
        ("Bitte schön", "عفواً / على الرحب والسعة", "مجاملات", "de-ar", "الرد على الشكر"),
        ("Entschuldigung", "معذرة / عذراً", "مجاملات", "de-ar", "لطلب العفو أو لفت الانتباه"),
        ("Ich verstehe nicht", "أنا لا أفهم", "مواقف يومية", "de-ar", "مفيدة جداً للمبتدئين"),
        ("Sprechen Sie Arabisch?", "هل تتحدث العربية؟", "مواقف يومية", "de-ar", "سؤال رسمي"),
        ("Wo ist der Bahnhof?", "أين تقع محطة القطار؟", "سفر ومواصلات", "de-ar", "سؤال عن الاتجاهات"),
        ("Was kostet das?", "كم يكلف هذا؟", "تسوق ومشتريات", "de-ar", "سؤال عن السعر"),
        ("Hilfe!", "النجدة / مساعدة!", "طوارئ", "de-ar", "في حالات الطوارئ")
    ]
    cur.executemany("""INSERT INTO cheatsheet_items
        (phrase, translation, category, languagePair, notes, createdAt)
        VALUES (?, ?, ?, ?, ?, strftime('%s', 'now') * 1000)""", cheatsheets)

    conn.commit()
    conn.close()

    db_size_mb = os.path.getsize(db_path) / (1024 * 1024)
    print(f"Database build COMPLETE! Path: {db_path}, Size: {db_size_mb:.2f} MB")

if __name__ == "__main__":
    main()
