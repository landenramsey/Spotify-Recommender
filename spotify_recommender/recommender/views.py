"""
View Functions for Spotify Recommender Application

This module contains all the view functions that handle HTTP requests.
Each function corresponds to a URL route and handles:
- User authentication with Spotify
- Fetching listening history from Spotify API
- Generating music recommendations
- Displaying data to users through templates

Flow Overview:
1. User visits home page -> clicks "Connect with Spotify"
2. User redirected to Spotify -> authorizes app -> callback with code
3. We exchange code for tokens -> store tokens -> create user -> redirect to dashboard
4. User can fetch listening history -> generate recommendations -> view results
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required  # Require login for certain views
from django.contrib.auth import login as auth_login  # Renamed to avoid conflict with spotify_login
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse  # For API responses
from django.views.decorators.http import require_http_methods  # Restrict HTTP methods
from django.conf import settings
from django.utils import timezone  # For timezone-aware datetime
from django.utils.dateparse import parse_datetime  # Parse datetime strings
from datetime import timedelta, datetime
import spotipy  # Spotify API library
from spotipy.oauth2 import SpotifyOAuth  # OAuth authentication
import os
from .models import SpotifyToken, SpotifyProfile, Track, ListeningHistory, Recommendation


# ============================================================================
# SPOTIFY OAUTH CONFIGURATION
# ============================================================================
# These values should be set as environment variables in production.
# For development, you can edit these directly or set them in your shell.

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', 'your_client_id_here')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', 'your_client_secret_here')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI', 'http://127.0.0.1:8000/callback/')

# Scopes define what permissions we request from Spotify
# user-read-recently-played: Get user's recently played tracks
# user-top-read: Get user's top tracks
# user-read-email: Get user's email address
# user-read-private: Get user's basic profile info
SCOPE = "user-read-recently-played user-top-read user-read-email user-read-private"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_spotify_oauth():
    """
    Creates and returns a SpotifyOAuth object for authentication.
    
    This object is used to:
    - Generate the authorization URL (where user logs in)
    - Exchange authorization code for access token
    - Refresh expired access tokens
    
    Returns:
        SpotifyOAuth: Configured OAuth object
    """
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPE,
        show_dialog=True  # Show Spotify login dialog even if user is already logged in
    )


def get_user_spotify_client(user):
    """
    Gets an authenticated Spotify API client for a user.
    
    This function:
    1. Retrieves the user's stored access token
    2. Checks if token is expired
    3. If expired, refreshes it using the refresh token
    4. Returns a spotipy.Spotify client ready to make API calls
    
    Args:
        user: Django User object
        
    Returns:
        spotipy.Spotify: Authenticated Spotify client, or None if user has no token
    """
    try:
        # Get user's stored token from database
        token_info = SpotifyToken.objects.get(user=user)
        
        # Check if token is expired (current time >= expiration time)
        if timezone.now() >= token_info.expires_at:
            # Token expired - refresh it using refresh token
            sp_oauth = get_spotify_oauth()
            token_info_data = sp_oauth.refresh_access_token(token_info.refresh_token)
            
            # Update stored token with new values
            token_info.access_token = token_info_data['access_token']
            token_info.expires_at = timezone.now() + timedelta(seconds=token_info_data['expires_in'])
            if 'refresh_token' in token_info_data:
                token_info.refresh_token = token_info_data['refresh_token']
            token_info.save()
        
        # Return authenticated Spotify client
        return spotipy.Spotify(auth=token_info.access_token)
    except SpotifyToken.DoesNotExist:
        # User hasn't authenticated with Spotify yet
        return None


# ============================================================================
# PUBLIC VIEWS (No login required)
# ============================================================================

def home(request):
    """
    Home page view - displays the landing page.
    
    This is the first page users see. It shows:
    - Welcome message
    - Feature highlights
    - "Connect with Spotify" button
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered home.html template
    """
    context = {
        'spotify_client_id': SPOTIFY_CLIENT_ID,
        'spotify_redirect_uri': SPOTIFY_REDIRECT_URI,
        'scope': SCOPE,
    }
    return render(request, 'recommender/home.html', context)


def spotify_login(request):
    """
    Initiates Spotify OAuth login flow.
    
    When user clicks "Connect with Spotify", this view:
    1. Creates OAuth object
    2. Gets authorization URL from Spotify
    3. Redirects user to Spotify login page
    
    User will authorize app, then Spotify redirects back to our callback URL.
    
    Args:
        request: HTTP request object
        
    Returns:
        Redirect to Spotify authorization page
    """
    sp_oauth = get_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()  # Get Spotify login URL
    return redirect(auth_url)  # Send user to Spotify


def spotify_callback(request):
    """
    Handles the callback from Spotify after user authorization.
    
    This is the most important authentication function:
    1. Spotify redirects here with authorization code (or error)
    2. We exchange code for access token
    3. We fetch user's profile from Spotify
    4. We create/update Django user and Spotify profile
    5. We store authentication tokens
    6. We log the user into Django
    7. We redirect to dashboard
    
    Args:
        request: HTTP request object (contains 'code' parameter from Spotify)
        
    Returns:
        Redirect to dashboard on success, error page on failure
    """
    # Get authorization code from URL parameters (Spotify sends this)
    code = request.GET.get('code')
    error = request.GET.get('error')  # Spotify sends 'error' if user denies access
    
    # Handle errors
    if error:
        return render(request, 'recommender/error.html', {'error': error})
    
    if not code:
        return render(request, 'recommender/error.html', {'error': 'No authorization code provided'})
    
    # Exchange authorization code for access token
    sp_oauth = get_spotify_oauth()
    token_info = sp_oauth.get_access_token(code)  # Get tokens from Spotify
    
    # Get user info from Spotify using the access token
    sp = spotipy.Spotify(auth=token_info['access_token'])
    spotify_user = sp.current_user()  # Get logged-in user's profile
    
    # Create or get Django user (use Spotify ID as username)
    username = spotify_user['id']  # Spotify user ID is unique
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': spotify_user.get('email', ''),
            'first_name': spotify_user.get('display_name', '').split()[0] if spotify_user.get('display_name') else '',
        }
    )
    
    # Save or update Spotify token (for future API calls)
    expires_at = timezone.now() + timedelta(seconds=token_info['expires_in'])
    spotify_token, _ = SpotifyToken.objects.update_or_create(
        user=user,
        defaults={
            'access_token': token_info['access_token'],
            'refresh_token': token_info.get('refresh_token', ''),
            'expires_at': expires_at,
            'token_type': token_info.get('token_type', 'Bearer'),
        }
    )
    
    # Save or update Spotify profile (name, email, picture, etc.)
    SpotifyProfile.objects.update_or_create(
        user=user,
        defaults={
            'spotify_id': spotify_user['id'],
            'display_name': spotify_user.get('display_name', ''),
            'email': spotify_user.get('email', ''),
            'country': spotify_user.get('country', ''),
            'profile_image_url': spotify_user['images'][0]['url'] if spotify_user.get('images') else '',
        }
    )
    
    # Log the user into Django (so they stay logged in)
    auth_login(request, user)
    
    # Redirect to dashboard (using namespace: 'recommender:dashboard')
    return redirect('recommender:dashboard')


# ============================================================================
# PROTECTED VIEWS (Login required)
# ============================================================================

@login_required
def dashboard(request):
    """
    Main dashboard view - shows user profile and action buttons.
    
    This is the main page users see after logging in. It displays:
    - User's Spotify profile (name, picture)
    - Button to fetch listening history
    - Button to generate recommendations
    - Links to view history and recommendations
    
    Args:
        request: HTTP request object (contains logged-in user)
        
    Returns:
        Rendered dashboard.html template
    """
    # Try to get user's Spotify profile (may not exist if something went wrong)
    try:
        profile = SpotifyProfile.objects.get(user=request.user)
    except SpotifyProfile.DoesNotExist:
        profile = None
    
    context = {
        'profile': profile,
    }
    return render(request, 'recommender/dashboard.html', context)


@login_required
@require_http_methods(["POST"])  # Only allow POST requests
def fetch_listening_history(request):
    """
    Fetches user's recent listening history from Spotify and stores it.
    
    This function:
    1. Gets authenticated Spotify client
    2. Calls Spotify API to get recently played tracks (last 50)
    3. For each track:
       - Creates Track record if it doesn't exist
       - Creates ListeningHistory entry
    4. Returns JSON response with results
    
    This is called via AJAX from the dashboard page.
    
    Args:
        request: HTTP request object (must be POST)
        
    Returns:
        JsonResponse with success status and count of items fetched
    """
    # Get authenticated Spotify client
    sp = get_user_spotify_client(request.user)
    if not sp:
        return JsonResponse({'error': 'Not authenticated with Spotify'}, status=401)
    
    try:
        # Fetch recently played tracks from Spotify (last 50)
        results = sp.current_user_recently_played(limit=50)
        
        tracks_created = 0  # Count new tracks added
        history_created = 0  # Count new history entries added
        
        # Process each track in the results
        for item in results['items']:
            track_data = item['track']
            
            # Create or get Track record (get_or_create prevents duplicates)
            # Handle preview_url - ensure it's not None (can be None from Spotify API)
            preview_url = track_data.get('preview_url') or ''
            album_cover_url = ''
            if track_data['album'].get('images'):
                album_cover_url = track_data['album']['images'][0]['url'] if track_data['album']['images'] else ''
            
            track, created = Track.objects.get_or_create(
                spotify_id=track_data['id'],
                defaults={
                    'name': track_data['name'],
                    'artist': ', '.join([artist['name'] for artist in track_data.get('artists', [])]),
                    'album': track_data['album']['name'],
                    'album_cover_url': album_cover_url,
                    'preview_url': preview_url,
                    'external_url': track_data.get('external_urls', {}).get('spotify', '') or '',
                    'duration_ms': track_data.get('duration_ms', 0),
                }
            )
            if created:
                tracks_created += 1
            
            # Create listening history entry
            # Parse the timestamp from Spotify (format: "2024-01-01T12:00:00Z")
            played_at_str = item['played_at'].replace('Z', '+00:00')
            played_at = parse_datetime(played_at_str)
            # Make timezone-aware if needed
            if played_at and timezone.is_naive(played_at):
                played_at = timezone.make_aware(played_at)
            
            # Create history entry (get_or_create prevents duplicates)
            _, history_created_flag = ListeningHistory.objects.get_or_create(
                user=request.user,
                track=track,
                played_at=played_at,
            )
            if history_created_flag:
                history_created += 1
        
        # Return success response with counts
        return JsonResponse({
            'success': True,
            'tracks_created': tracks_created,
            'history_entries_created': history_created,
            'message': f'Fetched {history_created} new listening history entries'
        })
    except Exception as e:
        # Return error response
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def generate_recommendations(request):
    """
    Generates personalized music recommendations based on user's listening history.
    
    This is the core recommendation algorithm:
    1. Gets user's top tracks from Spotify (their most played songs)
    2. Gets audio features for those tracks (danceability, energy, valence, tempo)
    3. Calculates average audio features (what type of music they like)
    4. Calls Spotify's recommendation API with:
       - Top tracks as "seed" (basis for recommendations)
       - Average features as "target" (match this style)
    5. Stores recommendations in database
    6. Redirects to recommendations page
    
    Args:
        request: HTTP request object
        
    Returns:
        Redirect to recommendations page on success, error page on failure
    """
    # Get authenticated Spotify client
    sp = get_user_spotify_client(request.user)
    if not sp:
        return JsonResponse({'error': 'Not authenticated with Spotify'}, status=401)
    
    try:
        # Get user's top tracks (medium_term = last 6 months)
        top_tracks = sp.current_user_top_tracks(limit=20, time_range='medium_term')
        
        # Get seed tracks (top 5) - these are the basis for recommendations
        seed_tracks = [track['id'] for track in top_tracks['items'][:5]]
        
        # Get audio features for seed tracks (danceability, energy, etc.)
        audio_features = sp.audio_features(seed_tracks)
        
        # Calculate average audio features (what type of music user likes)
        avg_features = {
            'danceability': sum(f['danceability'] for f in audio_features if f) / len(audio_features),
            'energy': sum(f['energy'] for f in audio_features if f) / len(audio_features),
            'valence': sum(f['valence'] for f in audio_features if f) / len(audio_features),
            'tempo': sum(f['tempo'] for f in audio_features if f) / len(audio_features),
        }
        
        # Get recommendations from Spotify API
        # seed_tracks: Songs similar to these
        # target_*: Match these audio feature values
        recommendations = sp.recommendations(
            seed_tracks=seed_tracks[:5],
            limit=20,  # Get 20 recommendations
            target_danceability=avg_features['danceability'],
            target_energy=avg_features['energy'],
            target_valence=avg_features['valence'],
            target_tempo=avg_features['tempo'],
        )
        
        # Clear old recommendations (so we only show new ones)
        Recommendation.objects.filter(user=request.user).delete()
        
        # Store new recommendations in database
        recommendations_created = 0
        for track_data in recommendations['tracks']:
            # Handle preview_url - ensure it's not None (can be None from Spotify API)
            preview_url = track_data.get('preview_url') or ''
            album_cover_url = ''
            if track_data['album'].get('images'):
                album_cover_url = track_data['album']['images'][0]['url'] if track_data['album']['images'] else ''
            
            # Create or get Track record
            track, _ = Track.objects.get_or_create(
                spotify_id=track_data['id'],
                defaults={
                    'name': track_data['name'],
                    'artist': ', '.join([artist['name'] for artist in track_data.get('artists', [])]),
                    'album': track_data['album']['name'],
                    'album_cover_url': album_cover_url,
                    'preview_url': preview_url,
                    'external_url': track_data.get('external_urls', {}).get('spotify', '') or '',
                    'duration_ms': track_data.get('duration_ms', 0),
                }
            )
            
            # Create recommendation record
            Recommendation.objects.create(
                user=request.user,
                track=track,
                score=0.8,  # Default confidence score
                reason="Based on your listening history and top tracks",
            )
            recommendations_created += 1
        
        # Redirect to recommendations page (using namespace)
        return redirect('recommender:recommendations')
    except Exception as e:
        # Show error page if something goes wrong
        return render(request, 'recommender/error.html', {'error': str(e)})


@login_required
def recommendations_view(request):
    """
    Displays all recommendations for the logged-in user.
    
    Shows a list of recommended tracks with:
    - Track name, artist, album
    - Album cover art
    - Preview audio player (if available)
    - Link to open in Spotify
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered recommendations.html template
    """
    # Get all recommendations for this user, ordered by score
    # select_related('track') optimizes database query (fetches track data in one query)
    recommendations = Recommendation.objects.filter(user=request.user).select_related('track')
    
    context = {
        'recommendations': recommendations,
    }
    return render(request, 'recommender/recommendations.html', context)


@login_required
def listening_history_view(request):
    """
    Displays user's listening history.
    
    Shows a list of recently played tracks with:
    - Track name, artist, album
    - Album cover art
    - When it was played
    - Link to open in Spotify
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered listening_history.html template
    """
    # Get last 100 listening history entries, ordered by most recent
    # select_related('track') optimizes database query
    history = ListeningHistory.objects.filter(user=request.user).select_related('track').order_by('-played_at')[:100]
    
    context = {
        'history': history,
    }
    return render(request, 'recommender/listening_history.html', context)
