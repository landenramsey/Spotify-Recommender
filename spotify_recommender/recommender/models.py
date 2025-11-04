"""
Database Models for Spotify Recommender Application

This module defines all the database models that store:
- User authentication tokens from Spotify
- User profile information from Spotify
- Track information (songs)
- User listening history
- Generated recommendations for users

Each model represents a table in the SQLite database and defines the structure
of the data we store about users and their music preferences.
"""

from django.db import models
from django.contrib.auth.models import User


class SpotifyToken(models.Model):
    """
    Stores Spotify OAuth authentication tokens for each user.
    
    This model is critical for maintaining user sessions with Spotify.
    When a user logs in via Spotify, we store their access token and refresh token here.
    Access tokens expire after 1 hour, so we use refresh tokens to get new ones.
    
    Fields:
    - user: One-to-one relationship with Django User (one token per user)
    - access_token: The token used to make API calls to Spotify
    - refresh_token: Used to get new access tokens when they expire
    - expires_at: When the access token expires (used to check if refresh is needed)
    - token_type: Usually "Bearer"
    - created_at: When this token record was created
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Delete token if user is deleted
    access_token = models.CharField(max_length=500)  # Token for API authentication
    refresh_token = models.CharField(max_length=500)  # Token to refresh access token
    expires_at = models.DateTimeField()  # When access token expires
    token_type = models.CharField(max_length=50)  # Usually "Bearer"
    created_at = models.DateTimeField(auto_now_add=True)  # Auto-set when created

    def __str__(self):
        """String representation for admin interface"""
        return f"{self.user.username}'s Spotify Token"


class SpotifyProfile(models.Model):
    """
    Stores additional Spotify profile information for each user.
    
    After a user authenticates with Spotify, we fetch their profile information
    (display name, email, profile picture, etc.) and store it here for quick access.
    This prevents us from having to make API calls every time we need the user's name.
    
    Fields:
    - user: One-to-one relationship with Django User
    - spotify_id: The user's unique Spotify ID (used as username in Django)
    - display_name: The user's Spotify display name
    - email: User's email (if available from Spotify)
    - country: User's country code (2 letters)
    - profile_image_url: URL to user's Spotify profile picture
    - created_at: When this profile was created
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Delete profile if user is deleted
    spotify_id = models.CharField(max_length=200, unique=True)  # Unique Spotify user ID
    display_name = models.CharField(max_length=200)  # User's display name on Spotify
    email = models.EmailField(blank=True)  # Email (optional, may not be provided)
    country = models.CharField(max_length=2, blank=True)  # Country code (optional)
    profile_image_url = models.URLField(blank=True)  # Profile picture URL
    created_at = models.DateTimeField(auto_now_add=True)  # Auto-set when created

    def __str__(self):
        """String representation for admin interface"""
        return f"{self.display_name} ({self.spotify_id})"


class Track(models.Model):
    """
    Stores information about individual tracks (songs).
    
    This is a central model that stores all track information we've seen.
    Multiple users can listen to the same track, so we store track data once
    and reference it from ListeningHistory and Recommendation models.
    
    Fields:
    - spotify_id: Unique Spotify track ID (primary identifier)
    - name: Track name
    - artist: Comma-separated list of artist names
    - album: Album name
    - album_cover_url: URL to album cover art
    - preview_url: URL to 30-second preview clip (if available)
    - external_url: Link to open track in Spotify app
    - duration_ms: Track length in milliseconds
    - created_at: When this track was first added to our database
    """
    spotify_id = models.CharField(max_length=200, unique=True)  # Unique Spotify track ID
    name = models.CharField(max_length=500)  # Track name
    artist = models.CharField(max_length=500)  # All artists (comma-separated)
    album = models.CharField(max_length=500, blank=True)  # Album name (optional)
    album_cover_url = models.URLField(blank=True)  # Album cover image URL
    preview_url = models.URLField(blank=True)  # 30-second preview audio URL
    external_url = models.URLField(blank=True)  # Link to track in Spotify app
    duration_ms = models.IntegerField(default=0)  # Track length in milliseconds
    created_at = models.DateTimeField(auto_now_add=True)  # Auto-set when created

    def __str__(self):
        """String representation for admin interface"""
        return f"{self.name} by {self.artist}"


class ListeningHistory(models.Model):
    """
    Stores individual listening events for each user.
    
    This model creates a record each time a user plays a track.
    It links users to tracks and stores when they were played.
    This data is used to analyze listening patterns and generate recommendations.
    
    Fields:
    - user: Foreign key to Django User (many history entries per user)
    - track: Foreign key to Track (many users can listen to same track)
    - played_at: When the track was played (timestamp from Spotify)
    - created_at: When we added this record to our database
    
    Meta options:
    - ordering: Order by most recent plays first
    - unique_together: Prevent duplicate entries for same user/track/time
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Many history entries per user
    track = models.ForeignKey(Track, on_delete=models.CASCADE)  # Reference to track
    played_at = models.DateTimeField()  # When track was played (from Spotify)
    created_at = models.DateTimeField(auto_now_add=True)  # When we added this record

    class Meta:
        # Order by most recent plays first (newest at top)
        ordering = ['-played_at']
        # Prevent duplicate entries: same user can't play same track at exact same time
        unique_together = ['user', 'track', 'played_at']

    def __str__(self):
        """String representation for admin interface"""
        return f"{self.user.username} - {self.track.name}"


class Recommendation(models.Model):
    """
    Stores music recommendations generated for each user.
    
    When we generate recommendations based on a user's listening history,
    we store them here so users can view them later. Each recommendation
    links a user to a track we think they'll like, with a score and reason.
    
    Fields:
    - user: Foreign key to Django User (many recommendations per user)
    - track: Foreign key to Track (track being recommended)
    - score: Recommendation confidence score (0.0 to 1.0, higher = better match)
    - reason: Text explanation of why this track was recommended
    - created_at: When this recommendation was generated
    
    Meta options:
    - ordering: Order by highest score first, then most recent
    - unique_together: One recommendation per user/track combination
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Many recommendations per user
    track = models.ForeignKey(Track, on_delete=models.CASCADE)  # Track being recommended
    score = models.FloatField(
        default=0.0,
        help_text="Recommendation confidence score (0.0 to 1.0)"
    )  # How confident we are in this recommendation
    reason = models.TextField(
        blank=True,
        help_text="Explanation of why this track was recommended"
    )  # Why we think they'll like it
    created_at = models.DateTimeField(auto_now_add=True)  # When recommendation was created

    class Meta:
        # Order by highest score first, then most recent
        ordering = ['-score', '-created_at']
        # One recommendation per user/track pair (avoid duplicates)
        unique_together = ['user', 'track']

    def __str__(self):
        """String representation for admin interface"""
        return f"Recommendation for {self.user.username}: {self.track.name}"
