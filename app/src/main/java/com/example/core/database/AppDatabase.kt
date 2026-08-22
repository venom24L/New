package com.example.core.database

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase

@Database(
    entities = [
        WordEntity::class,
        GermanNounEntity::class,
        GermanVerbEntity::class,
        ExampleEntity::class,
        HistoryEntity::class,
        CheatSheetEntity::class,
        ConjugationEntity::class
    ],
    version = 3,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {

    abstract fun wordDao(): WordDao
    abstract fun germanNounDao(): GermanNounDao
    abstract fun germanVerbDao(): GermanVerbDao
    abstract fun exampleDao(): ExampleDao
    abstract fun historyDao(): HistoryDao
    abstract fun cheatSheetDao(): CheatSheetDao
    abstract fun conjugationDao(): ConjugationDao

    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null

        val MIGRATION_1_2 = object : Migration(1, 2) {
            override fun migrate(db: SupportSQLiteDatabase) {
                // Drop obsolete review_schedule table safely if it existed
                db.execSQL("DROP TABLE IF EXISTS review_schedule")
                
                // Drop redundant translation_history table safely if it existed
                db.execSQL("DROP TABLE IF EXISTS translation_history")

                // Update history table safely to add source_language and target_language columns if they don't exist
                try {
                    db.execSQL("ALTER TABLE history ADD COLUMN source_language TEXT NOT NULL DEFAULT 'de'")
                } catch (_: Exception) {}

                try {
                    db.execSQL("ALTER TABLE history ADD COLUMN target_language TEXT NOT NULL DEFAULT 'ar'")
                } catch (_: Exception) {}

                // Ensure fast index on query in history table
                try {
                    db.execSQL("CREATE INDEX IF NOT EXISTS index_history_query ON history(query)")
                } catch (_: Exception) {}
            }
        }

        val MIGRATION_2_3 = object : Migration(2, 3) {
            override fun migrate(db: SupportSQLiteDatabase) {
                // Recreate history table without foreign key constraint and with new index
                try {
                    db.execSQL("""
                        CREATE TABLE IF NOT EXISTS `history_new` (
                            `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                            `word_id` INTEGER,
                            `query` TEXT NOT NULL,
                            `source_language` TEXT NOT NULL,
                            `target_language` TEXT NOT NULL,
                            `result_type` TEXT NOT NULL,
                            `result_text` TEXT NOT NULL,
                            `is_saved` INTEGER NOT NULL,
                            `searched_at` INTEGER NOT NULL
                        )
                    """)
                    db.execSQL("""
                        INSERT OR IGNORE INTO `history_new` 
                        SELECT `id`, `word_id`, `query`, `source_language`, `target_language`, `result_type`, `result_text`, `is_saved`, `searched_at` 
                        FROM `history`
                    """)
                    db.execSQL("DROP TABLE IF EXISTS `history`")
                    db.execSQL("ALTER TABLE `history_new` RENAME TO `history`")
                    db.execSQL("CREATE INDEX IF NOT EXISTS `index_history_searched_at` ON `history` (`searched_at`)")
                    db.execSQL("CREATE INDEX IF NOT EXISTS `index_history_word_id` ON `history` (`word_id`)")
                    db.execSQL("CREATE INDEX IF NOT EXISTS `index_history_query` ON `history` (`query`)")
                    db.execSQL("CREATE INDEX IF NOT EXISTS `index_history_is_saved` ON `history` (`is_saved`)")
                } catch (_: Exception) {}
            }
        }

        fun getInstance(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val appContext = context.applicationContext
                val builder = Room.databaseBuilder(
                    appContext,
                    AppDatabase::class.java,
                    "deutschar.db"
                )

                val hasAsset = try {
                    val assetsList = appContext.assets.list("databases")
                    assetsList != null && assetsList.contains("deutschar.db")
                } catch (_: Throwable) {
                    false
                }

                if (hasAsset) {
                    builder.createFromAsset("databases/deutschar.db")
                }

                val instance = builder
                    .addMigrations(MIGRATION_1_2, MIGRATION_2_3)
                    .fallbackToDestructiveMigration()
                    .build()

                INSTANCE = instance
                instance
            }
        }
    }
}
