# Spotify Recommender

A Django web application that provides personalized music recommendations based on your Spotify listening history.

## Features

- 🔐 **Spotify OAuth Authentication** - Secure login with your Spotify account
- 📊 **Listening History Analysis** - Fetch and analyze your recent listening patterns
- 🎯 **Personalized Recommendations** - Get song recommendations tailored to your music taste
- 🎵 **Track Discovery** - Discover new artists and songs based on your preferences
- 📱 **Modern UI** - Beautiful, responsive user interface

## Prerequisites

- Python 3.8 or higher
- Django 4.2.7 or higher
- Spotify Developer Account (for API credentials)

## Setup Instructions

### 1. Get Spotify API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Note down your **Client ID** and **Client Secret**
4. Add `http://127.0.0.1:8000/callback/` to your **Redirect URIs**

   **Important**: Spotify has updated their redirect URI validation requirements (effective April 9, 2025, with migration deadline of November 2025). For local development, you must use `127.0.0.1` instead of `localhost`. The redirect URI must be:
   - A loopback IP address (e.g., `http://127.0.0.1:8000/callback/`) for local development, OR
   - An HTTPS URL for production
   - Exact match required (trailing slashes matter)

### 2. Install Dependencies

**Important**: All Django commands should be run from the `spotify_recommender/` directory (the folder that contains `manage.py`).

From the project root directory:
```bash
cd spotify_recommender
pip install -r requirements.txt
```

### 3. Set Environment Variables

**Option 1: Set Environment Variables**

For **bash/zsh** (macOS/Linux):
```bash
export SPOTIFY_CLIENT_ID='your_client_id_here'
export SPOTIFY_CLIENT_SECRET='your_client_secret_here'
export SPOTIFY_REDIRECT_URI='http://127.0.0.1:8000/callback/'
```

For **PowerShell** (Windows):
```powershell
$env:SPOTIFY_CLIENT_ID='your_client_id_here'
$env:SPOTIFY_CLIENT_SECRET='your_client_secret_here'
$env:SPOTIFY_REDIRECT_URI='http://127.0.0.1:8000/callback/'
```

**Option 2: Edit views.py directly** (Easiest for getting started)

Alternatively, you can edit `spotify_recommender/recommender/views.py` and replace the placeholder values directly (lines 19-21):
- Replace `'your_client_id_here'` with your Spotify Client ID
- Replace `'your_client_secret_here'` with your Spotify Client Secret

Note: This is fine for development, but use environment variables for production.

### 4. Run Database Migrations

**Note**: Make sure you're in the `spotify_recommender/` directory (where `manage.py` is located).

From the project root directory:
```bash
cd spotify_recommender
python manage.py makemigrations
python manage.py migrate
```

### 5. Create a Superuser (Optional)

```bash
# Make sure you're in the spotify_recommender/ directory
python manage.py createsuperuser
```

### 6. Run the Development Server

```bash
# Make sure you're in the spotify_recommender/ directory
python manage.py runserver
```

**Quick Tip**: If you're activating a virtual environment, you can do it all in one command:
```bash
cd spotify_recommender
source ../venv/bin/activate  # Adjust path if your venv is in a different location
python manage.py runserver
```

### 7. Access the Application

Open your browser and navigate to:
- **Home Page**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/

## Usage

1. **Connect with Spotify**: Click "Connect with Spotify" on the home page
2. **Authorize the App**: Authorize the app to access your Spotify data
3. **Fetch Listening History**: On the dashboard, click "Fetch History" to import your recent listening history
4. **Generate Recommendations**: Click "Generate Recommendations" to get personalized song suggestions
5. **View Recommendations**: Browse your recommendations and discover new music!

## Project Structure

```
spotify_recommender/
├── recommender/
│   ├── models.py          # Database models
│   ├── views.py           # View functions
│   ├── urls.py            # URL routing
│   ├── admin.py           # Admin interface
│   ├── templates/         # HTML templates
│   └── static/css/        # CSS styles
├── spotify_recommender/
│   ├── settings.py        # Django settings
│   └── urls.py            # Main URL configuration
└── requirements.txt       # Python dependencies
```

## Models

- **SpotifyToken**: Stores OAuth tokens for users
- **SpotifyProfile**: Stores user's Spotify profile information
- **Track**: Stores track information
- **ListeningHistory**: Stores user's listening history
- **Recommendation**: Stores generated recommendations

## API Scopes Used

The application requests the following Spotify API scopes:
- `user-read-recently-played` - Read recently played tracks
- `user-top-read` - Read user's top tracks
- `user-read-email` - Read user's email
- `user-read-private` - Read user's private information

## Troubleshooting

### Issue: "Invalid redirect URI"
- Make sure you've added `http://127.0.0.1:8000/callback/` to your Spotify app's redirect URIs (use `127.0.0.1` instead of `localhost` to comply with Spotify's new validation requirements)

### Issue: "Invalid client credentials"
- Verify your `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` are correct
- Make sure they're set as environment variables or in the code

### Issue: "Token expired"
- The app automatically refreshes tokens, but if you see this error, try logging in again

## Future Enhancements

- [ ] Add more sophisticated recommendation algorithms
- [ ] Support for playlists
- [ ] Export recommendations to Spotify playlists
- [ ] Music genre analysis
- [ ] Listening statistics and charts
- [ ] Social features (share recommendations)

## License

This project is open source and available for personal and educational use.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

