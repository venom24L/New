package com.example

import android.animation.ObjectAnimator
import android.os.Bundle
import android.view.View
import android.view.animation.AccelerateDecelerateInterpolator
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.core.animation.doOnEnd
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.lifecycle.ViewModelProvider
import com.example.core.database.AppDatabase
import com.example.core.database.WordRepositoryImpl
import com.example.core.translation.OfflineTranslationService
import com.example.feature.search.SearchScreen
import com.example.feature.search.SearchViewModel
import com.example.ui.theme.DeutschArabischTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        val splashScreen = installSplashScreen()

        // Safe splash screen exit animation
        try {
            splashScreen.setOnExitAnimationListener { splashScreenViewProvider ->
                try {
                    val fadeOut = ObjectAnimator.ofFloat(
                        splashScreenViewProvider.view,
                        View.ALPHA,
                        1f,
                        0f
                    ).apply {
                        interpolator = AccelerateDecelerateInterpolator()
                        duration = 200L
                        doOnEnd { 
                            try {
                                splashScreenViewProvider.remove()
                            } catch (_: Exception) {}
                        }
                    }
                    fadeOut.start()
                } catch (_: Exception) {
                    try {
                        splashScreenViewProvider.remove()
                    } catch (_: Exception) {}
                }
            }
        } catch (_: Exception) {}

        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        val db = AppDatabase.getInstance(applicationContext)
        val wordRepository = WordRepositoryImpl(
            wordDao = db.wordDao(),
            conjugationDao = db.conjugationDao(),
            exampleDao = db.exampleDao(),
            historyDao = db.historyDao(),
            nounDao = db.germanNounDao(),
            verbDao = db.germanVerbDao()
        )
        val translationService = OfflineTranslationService(applicationContext)
        val viewModelFactory = SearchViewModel.Factory(
            wordRepository = wordRepository,
            translationService = translationService
        )
        val viewModel = ViewModelProvider(this, viewModelFactory)[SearchViewModel::class.java]

        setContent {
            DeutschArabischTheme {
                SearchScreen(viewModel = viewModel)
            }
        }
    }
}
