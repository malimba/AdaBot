import sqlite3
import json
from collections import defaultdict
from typing import Dict, Any, List
import string
import nltk 
from gensim import corpora, models
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize

#downloads
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

class CustomPersistence:
    def __init__(self, db_filename: str = 'custom_persistence.db'):
        self.db_filename = db_filename
        self.user_data: Dict[int, Dict[str, Any]] = {}
        self._initialize_database()

    def _initialize_database(self) -> None:
        with sqlite3.connect(self.db_filename) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    data TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    user_id INTEGER,
                    note_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS lesson_plans (
                    user_id INTEGER,
                    note_id INTEGER,
                    lesson_plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT,
                    details TEXT,
                    FOREIGN KEY (note_id) REFERENCES notes (note_id),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
    def initialize_user(self, user_id:int, username: str) -> bool:
        with sqlite3.connect(self.db_filename) as conn:
            cursor = conn.cursor()
             # Check if user is in the table
            cursor.execute('SELECT * FROM users WHERE user_id=?', (user_id,))
            user = cursor.fetchone()
            if user is None:
                # If user not in table, insert user with chat_id as user_id
                cursor.execute('INSERT INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
                conn.commit()
                return False 
            else:
                return True


    def save_user_data(self, user_id: int, data: Dict[str, Any]) -> None:
        with sqlite3.connect(self.db_filename) as conn:
            cursor = conn.cursor()
            cursor.execute('REPLACE INTO users (user_id, username, data) VALUES (?, ?, ?)',
               (user_id, username, json.dumps(data)))


    def load_user_data(self, user_id: int) -> Dict[str, Any]:
        with sqlite3.connect(self.db_filename) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT username FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            if result:
                json_formatted_string = f'"{result[0]}"'
                return json.loads(json_formatted_string)
            else:
                return {}

    def get_all_user_data(self) -> Dict[int, Dict[str, Any]]:
        with sqlite3.connect(self.db_filename) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users')
            rows = cursor.fetchall()
            for row in rows:
                user_id, data_json = row
                self.user_data[user_id] = json.loads(data_json)
        return self.user_data

    def save_note(self, user_id: int, content: str) -> None:
        with sqlite3.connect(self.db_filename) as conn:
            conn.execute('INSERT INTO notes (user_id, content) VALUES (?, ?)',
                         (user_id, content))
            
        

    def get_notes(self, user_id: int) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_filename) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM notes WHERE user_id = ?', (user_id,))
            rows = cursor.fetchall()
            return [{'note_id': note_id, 'content': content} for _, note_id, content in rows]

    def save_lesson_plan(self, user_id: int, lesson_plan_id: int, topic: str, details: str) -> None:
        with sqlite3.connect(self.db_filename) as conn:
            conn.execute('INSERT INTO lesson_plans (user_id, lesson_plan_id, topic, details) VALUES (?, ?, ?, ?)',
                         (user_id, lesson_plan_id, topic, details))

    def get_lesson_plans(self, user_id: int) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_filename) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM lesson_plans WHERE user_id = ?', (user_id,))
            rows = cursor.fetchall()
            return [{'lesson_plan_id': lesson_plan_id, 'topic': topic, 'details': details} for _, lesson_plan_id, topic, details in rows]


class Notes:
    def __init__(self, db_filename:str):
        self.db_filename = db_filename

    def process_notes(self, notes_content:str, user_id:int):
        #perform LDA on notes
        processed_notes = self.preprocess_notes(notes_content)
        lda_model = self.train_lda_model(processed_notes)

        # Extract main topics
        main_topics = self.extract_main_topics(lda_model) #commit notes to database, retrieve id
        print('Main topics: ', main_topics)
        # Create a tailored learning plan based on topics
        lesson_plans = self.create_learning_plan(lda_model)
        print('Leson Plans: ', lesson_plans)
        #initialise databse connection
        conn = sqlite3.connect(self.db_filename)
        cursor = conn.cursor()

        #retrieving last notes entry id
        note_id = cursor.execute('SELECT MAX(note_id) FROM notes LIMIT 1').fetchone()[0]
        print(note_id)
        # # Save learning plan to the database
        main_topics = str(main_topics)
        lesson_plans1 = lesson_plans
        lesson_plans2 = str(lesson_plans)
        cursor.execute('INSERT INTO lesson_plans (topic, details, note_id, user_id) VALUES (?, ?, ?, ?)', (main_topics, lesson_plans2, note_id, user_id))
        conn.commit()
        return lesson_plans
    def preprocess_notes(self, notes_content):
        #removing stop words, tokenizing, etc
        #Tokenization
        words = word_tokenize(notes_content)

        #lowercase everything
        words = [word.lower() for word in words]
        #remove stop words
        stop_words = set(stopwords.words('english'))
        words = [word for word in words if word not in stop_words]

        # Lemmatization (an alternative to stemming)
        lemmatizer = nltk.stem.WordNetLemmatizer()
        words = [lemmatizer.lemmatize(word) for word in words]
        #Join processed text(words)
        processed_text = ''.join(words)
        print('PROCESSED TEXT: ', processed_text)
        return words

    def train_lda_model(self, processed_notes):
        tokenized_notes = [document.split() for document in processed_notes]
        dictionary = corpora.Dictionary(tokenized_notes)
        #convert each document to bag of words
        bow_corpus = [dictionary.doc2bow(note) for note in tokenized_notes]
        #train lda model
        lda_model = models.LdaModel(bow_corpus, num_topics=5, id2word=dictionary) #considering increasing topic list to fit larger criteria when explanding project
        return lda_model
    def extract_main_topics(self, lda_model):
        # Use get_topic_terms to get topics with weights
        main_topics = [lda_model.get_topic_terms(topic, topn=10) for topic in range(lda_model.num_topics)]
        return main_topics

    def create_learning_plan(self, lda_model):
        num_days = 5
        learning_plan = {}
        #translation table to remove punctuations
        translator = str.maketrans('', '', string.punctuation)
        for day in range(1, num_days + 1):
            topics = lda_model.get_topic_terms(day - 1, topn=10)  # Use get_topic_terms to get topics with weights
            top_word_id, _ = max(topics, key=lambda x: x[1])#choose word with the heighest weight as most relevant
            top_word = lda_model.id2word[top_word_id].translate(translator) #convert word id to word
            if top_word.isspace() or top_word == '':
                learning_plan[day] = {'topic': f'Topic {day}: Rest'}    
            else:
                learning_plan[day] = {'topic': f'Topic {day}: {top_word}'}
        return learning_plan
    def pretty_print_topic_list(tList):
        pretty_topics = {f'Topic {day}': topic['topic'] for day, topic in tList.items()}
        print(json.dumps(pretty_topics, indent=2))

