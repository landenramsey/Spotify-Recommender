"""
URL Configuration for Recommender App

This file maps URL paths to view functions. When a user visits a URL,
Django uses this file to determine which view function to call.

URL Patterns:
- '' (empty) -> home page
- 'login/' -> initiate Spotify login
- 'callback/' -> handle Spotify OAuth callback
- 'dashboard/' -> main dashboard (requires login)
- 'fetch-history/' -> fetch listening history (requires login, POST only)
- 'generate-recommendations/' -> generate recommendations (requires login)
- 'recommendations/' -> view recommendations (requires login)
- 'history/' -> view listening history (requires login)

The app_name = 'recommender' creates a namespace, so URLs are referenced
as 'recommender:home', 'recommender:dashboard', etc.
"""

from django.urls import path
from . import views

# Namespace for URL reversing (prevents conflicts with other apps)
app_name = 'recommender'

# URL patterns: path('URL', view_function, name='url_name')
urlpatterns = [
    # Home page - landing page with "Connect with Spotify" button
    path('', views.home, name='home'),
    
    # Spotify OAuth login - redirects user to Spotify authorization page
    path('login/', views.spotify_login, name='spotify_login'),
    
    # Spotify OAuth callback - handles return from Spotify after authorization
    path('callback/', views.spotify_callback, name='spotify_callback'),
    
    # Dashboard - main page after login, shows profile and action buttons
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Fetch listening history - AJAX endpoint to fetch and store listening history
    path('fetch-history/', views.fetch_listening_history, name='fetch_history'),
    
    # Generate recommendations - creates recommendations based on listening history
    path('generate-recommendations/', views.generate_recommendations, name='generate_recommendations'),
    
    # View recommendations - displays all recommendations for the user
    path('recommendations/', views.recommendations_view, name='recommendations'),
    
    # View listening history - displays user's listening history
    path('history/', views.listening_history_view, name='listening_history'),
]
