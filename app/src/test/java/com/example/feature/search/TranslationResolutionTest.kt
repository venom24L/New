package com.example.feature.search

import com.example.core.database.GermanNounDao
import com.example.core.database.GermanNounEntity
import com.example.core.database.GermanVerbDao
import com.example.core.database.GermanVerbEntity
import com.example.core.database.WordDao
import com.example.core.database.WordEntity
import com.example.core.translation.LanguageDetector
import com.example.core.translation.MlKitTranslatorManager
import com.example.core.translation.TriLanguageRepository
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class TranslationResolutionTest {

    private val dummyNounDao = object : GermanNounDao {
        override suspend fun findByLemma(lemma: String) = null
        override suspend fun findByPlural(plural: String) = null
        override suspend fun getById(id: Long) = null
        override suspend fun insert(noun: GermanNounEntity) = 0L
        override suspend fun insertNouns(nouns: List<GermanNounEntity>) = emptyList<Long>()
    }

    private val dummyVerbDao = object : GermanVerbDao {
        override suspend fun findByInfinitive(infinitive: String) = null
        override suspend fun findByForm(verb: String) = null
        override suspend fun insert(verb: GermanVerbEntity) = 0L
        override suspend fun insertVerbs(verbs: List<GermanVerbEntity>) = emptyList<Long>()
    }

    @Test
    fun testLanguageDetectorArabicDetection() {
        assertTrue(LanguageDetector.hasArabicCharacters("يتعايش"))
        assertTrue(LanguageDetector.hasArabicCharacters("التعايش"))
        assertTrue(LanguageDetector.hasArabicCharacters("بيت / منزل"))
        assertFalse(LanguageDetector.hasArabicCharacters("to coexist"))
        assertFalse(LanguageDetector.hasArabicCharacters("house"))
        assertFalse(LanguageDetector.hasArabicCharacters("koexistieren"))
    }

    @Test
    fun testTriLanguageWithEnglishGlossInDatabase() = runBlocking {
        // Mock WordDao with a word that has an English gloss in the DB (like koexistieren)
        val mockWordDao = object : WordDao {
            override suspend fun getById(id: Long) = null
            override suspend fun findByGermanWordExact(word: String): WordEntity? =
                if (word.equals("koexistieren", ignoreCase = true)) {
                    WordEntity(
                        id = 1,
                        germanWord = "koexistieren",
                        wordType = "verb",
                        arabicTranslation = "to coexist" // Stored English gloss
                    )
                } else null

            override suspend fun findExactIgnoreCase(word: String): WordEntity? = findByGermanWordExact(word)
            override suspend fun findByPluralIgnoreCase(plural: String): WordEntity? = null
            override suspend fun searchWords(query: String, limit: Int) = emptyList<WordEntity>()
            override suspend fun getSuggestions(prefix: String, limit: Int) = emptyList<String>()
            override suspend fun findByArabic(arabic: String, limit: Int) = emptyList<WordEntity>()
            override suspend fun getVocabularyList(limit: Int) = emptyList<WordEntity>()
            override suspend fun getAllWordsList() = emptyList<WordEntity>()
            override suspend fun countWords() = 1
            override suspend fun insertWord(word: WordEntity) = 1L
            override suspend fun insert(word: WordEntity) = 1L
            override suspend fun insertAll(words: List<WordEntity>) = listOf(1L)
        }

        val mockMlKit = object : MlKitTranslatorManager() {
            override suspend fun translateDirect(text: String, sourceLang: String, targetLang: String): String {
                return when {
                    sourceLang == "de" && targetLang == "en" -> "to coexist"
                    sourceLang == "en" && targetLang == "ar" -> "يتعايش"
                    sourceLang == "de" && targetLang == "ar" -> "يتعايش"
                    else -> text
                }
            }
        }

        val repo = TriLanguageRepository(
            germanNounDao = dummyNounDao,
            germanVerbDao = dummyVerbDao,
            wordDao = mockWordDao,
            mlKitTranslator = mockMlKit
        )

        val resultTry = repo.translateTriLanguage("koexistieren")
        if (resultTry.isFailure) {
            resultTry.exceptionOrNull()?.printStackTrace()
            throw resultTry.exceptionOrNull() ?: Exception("Unknown error")
        }
        val result = resultTry.getOrThrow()

        // Verify Arabic and English are NOT identical
        assertNotEquals("Arabic translation should not match English string", result.english, result.arabic)
        assertTrue("Arabic translation must contain Arabic characters", LanguageDetector.hasArabicCharacters(result.arabic))
        assertEquals("to coexist", result.english)
        assertEquals("يتعايش", result.arabic)
    }

    @Test
    fun testTriLanguageWithRealArabicInDatabase() = runBlocking {
        val mockWordDao = object : WordDao {
            override suspend fun getById(id: Long) = null
            override suspend fun findByGermanWordExact(word: String): WordEntity? =
                if (word.equals("Haus", ignoreCase = true)) {
                    WordEntity(
                        id = 2,
                        germanWord = "Haus",
                        article = "das",
                        plural = "Häuser",
                        wordType = "noun",
                        arabicTranslation = "بيت / منزل"
                    )
                } else null

            override suspend fun findExactIgnoreCase(word: String): WordEntity? = findByGermanWordExact(word)
            override suspend fun findByPluralIgnoreCase(plural: String): WordEntity? = null
            override suspend fun searchWords(query: String, limit: Int) = emptyList<WordEntity>()
            override suspend fun getSuggestions(prefix: String, limit: Int) = emptyList<String>()
            override suspend fun findByArabic(arabic: String, limit: Int) = emptyList<WordEntity>()
            override suspend fun getVocabularyList(limit: Int) = emptyList<WordEntity>()
            override suspend fun getAllWordsList() = emptyList<WordEntity>()
            override suspend fun countWords() = 1
            override suspend fun insertWord(word: WordEntity) = 1L
            override suspend fun insert(word: WordEntity) = 1L
            override suspend fun insertAll(words: List<WordEntity>) = listOf(1L)
        }

        val mockMlKit = object : MlKitTranslatorManager() {
            override suspend fun translateDirect(text: String, sourceLang: String, targetLang: String): String {
                return when {
                    sourceLang == "de" && targetLang == "en" -> "house"
                    sourceLang == "en" && targetLang == "ar" -> "بيت"
                    else -> text
                }
            }
        }

        val repo = TriLanguageRepository(
            germanNounDao = dummyNounDao,
            germanVerbDao = dummyVerbDao,
            wordDao = mockWordDao,
            mlKitTranslator = mockMlKit
        )

        val result = repo.translateTriLanguage("Haus").getOrThrow()

        assertEquals("house", result.english)
        assertEquals("بيت / منزل", result.arabic)
        assertTrue(LanguageDetector.hasArabicCharacters(result.arabic))
    }

    private fun assertEquals(expected: String, actual: String) {
        org.junit.Assert.assertEquals(expected, actual)
    }
}
