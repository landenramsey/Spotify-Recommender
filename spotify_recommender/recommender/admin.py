"""
Django Admin Interface Configuration

This module registers all our models with Django's admin interface.
The admin interface allows you to view, edit, and manage all data in the database
through a web interface at /admin/ (requires superuser login).

Each model gets its own admin class that customizes:
- Which fields are displayed in the list view
- Which fields can be filtered
- Which fields can be searched
"""

from django.contrib import admin
from .models import SpotifyToken, SpotifyProfile, Track, ListeningHistory, Recommendation


@admin.register(SpotifyToken)
class SpotifyTokenAdmin(admin.ModelAdmin):
    """
    Admin configuration for SpotifyToken model.
    
    Customizes how token data appears in the Django admin panel.
    - list_display: Shows these columns in the list view
    - list_filter: Adds filter sidebar for these fields
    - search_fields: Makes these fields searchable
    """
    list_display = ('user', 'token_type', 'expires_at', 'created_at')  # Columns shown in list
    list_filter = ('token_type', 'created_at')  # Filter options in sidebar
    search_fields = ('user__username', 'user__email')  # Fields you can search by


@admin.register(SpotifyProfile)
class SpotifyProfileAdmin(admin.ModelAdmin):
    """
    Admin configuration for SpotifyProfile model.
    
    Allows easy viewing and searching of user profiles in the admin panel.
    """
    list_display = ('user', 'spotify_id', 'display_name', 'country', 'created_at')
    list_filter = ('country', 'created_at')  # Filter by country or date
    search_fields = ('user__username', 'display_name', 'spotify_id')  # Search by any of these


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    """
    Admin configuration for Track model.
    
    Makes it easy to browse and search all tracks in the database.
    """
    list_display = ('name', 'artist', 'album', 'spotify_id', 'created_at')
    list_filter = ('created_at',)  # Filter by when track was added
    search_fields = ('name', 'artist', 'album', 'spotify_id')  # Search by track info


@admin.register(ListeningHistory)
class ListeningHistoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for ListeningHistory model.
    
    Provides a date hierarchy navigation to browse listening history by date.
    """
    list_display = ('user', 'track', 'played_at', 'created_at')
    list_filter = ('played_at', 'created_at')  # Filter by play date or creation date
    search_fields = ('user__username', 'track__name', 'track__artist')
    date_hierarchy = 'played_at'  # Adds year/month/day navigation at top


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    """
    Admin configuration for Recommendation model.
    
    Allows viewing all recommendations generated for users, sorted by score.
    """
    list_display = ('user', 'track', 'score', 'created_at')  # Show recommendation score
    list_filter = ('score', 'created_at')  # Filter by score or date
    search_fields = ('user__username', 'track__name', 'track__artist')
    date_hierarchy = 'created_at'  # Browse by when recommendation was created
