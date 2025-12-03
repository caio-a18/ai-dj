"""
Playlist generation logic using ML model and Spotify integration
"""
import os
import uuid
from decimal import Decimal
import requests
import librosa
import numpy as np
import torch
import pandas as pd
import spotipy
from dotenv import load_dotenv

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '../../../data/.env'))

# -------------------------------------------------------------------
# Model Definition
# -------------------------------------------------------------------
class MelFeatureEmbedding(torch.nn.Module):
    def __init__(self, input_dim=64, embedding_dim=64, num_classes=10):
        super().__init__()
        self.fc1 = torch.nn.Linear(input_dim, 128)
        self.fc2 = torch.nn.Linear(128, embedding_dim)
        self.classifier = torch.nn.Linear(embedding_dim, num_classes)
        self.dropout = torch.nn.Dropout(0.2)

    def forward(self, x):
        x = torch.nn.functional.relu(self.fc1(x))
        x = self.dropout(x)
        emb = self.fc2(x)
        logits = self.classifier(emb)
        return logits, emb


# Load model
MODEL_PATH = os.path.join(os.path.dirname(__file__), '../../../data/mel_embedding_model.pth')
model = MelFeatureEmbedding(input_dim=64, embedding_dim=64, num_classes=10)
if os.path.exists(MODEL_PATH):
    model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
    print(f"✓ Loaded model weights from {MODEL_PATH}")
else:
    print(f"⚠ Model file not found: {MODEL_PATH}")
model.eval()


# -------------------------------------------------------------------
# Deezer Audio Feature Extraction
# -------------------------------------------------------------------
def get_deezer_preview_url(track_name, artist_name=None):
    """Get preview URL from Deezer API"""
    query = f"{track_name}"
    if artist_name:
        query += f" {artist_name}"
    url = f"https://api.deezer.com/search/track?q={query}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Deezer API request failed with status {response.status_code}")
        return None
    try:
        data = response.json()
        if 'data' in data and data['data']:
            return data['data'][0].get('preview')
    except ValueError:
        print(f"Invalid JSON response from Deezer")
    return None


def download_preview(preview_url, output_filename):
    """Download audio preview"""
    response = requests.get(preview_url)
    with open(output_filename, 'wb') as f:
        f.write(response.content)


def extract_mel_spectrogram_features(filename, n_mels=32, fmax=8000):
    """Extract mel spectrogram features from audio file"""
    y, sr = librosa.load(filename, sr=None)
    mel_spect = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=n_mels, fmax=fmax)
    mel_spect_db = librosa.power_to_db(mel_spect, ref=np.max)
    return np.concatenate((mel_spect_db.mean(axis=1), mel_spect_db.std(axis=1)))


def process_user_input_song(track_title, artist_name=None):
    """Extract features from user's input song"""
    print(f"Processing: '{track_title}' by '{artist_name}'")
    preview_url = get_deezer_preview_url(track_title, artist_name)
    if preview_url:
        tmp_filename = f'temp_{track_title[:10].replace(" ", "_")}.mp3'
        try:
            download_preview(preview_url, tmp_filename)
            features = extract_mel_spectrogram_features(tmp_filename)
            os.remove(tmp_filename)
            print(f"✓ Extracted features for '{track_title}'")
            return features
        except Exception as e:
            print(f"Error processing {track_title}: {e}")
            return None
    else:
        print(f"No preview URL found for: {track_title}")
        return None


# -------------------------------------------------------------------
# DynamoDB Integration
# -------------------------------------------------------------------
def load_dataset_from_dynamodb(datasets_table):
    """Load all songs from DynamoDB datasets table"""
    print("Loading dataset from DynamoDB...")
    response = datasets_table.scan()
    items = response['Items']
    while 'LastEvaluatedKey' in response:
        response = datasets_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])
    
    df = pd.DataFrame(items)
    print(f"✓ Loaded {len(df)} songs from dataset")
    return df


def get_recommendations(new_song_features, df, model, number_of_songs):
    """Get song recommendations using cosine similarity"""
    feature_cols = [f"mel_feat_{i}" for i in range(64)]
    titles = df['track_title'].tolist()
    artists_names = df['artist_name'].tolist()
    features = df[feature_cols].values.astype('float32')
    features_tensor = torch.tensor(features)
    
    # Compute embeddings for all existing tracks
    with torch.no_grad():
        _, all_embeddings = model(features_tensor)
    
    # Compute query embedding
    query_features = torch.tensor(new_song_features, dtype=torch.float32).unsqueeze(0)
    with torch.no_grad():
        _, query_embedding = model(query_features)
    
    # Compute similarities
    cos = torch.nn.CosineSimilarity(dim=1)
    similarities = cos(query_embedding, all_embeddings)
    sorted_indices = torch.argsort(similarities, descending=True).tolist()
    
    # Filter and return top recommendations
    extra_recs = 10
    total_recs = number_of_songs + extra_recs
    recommendations = []
    for idx in sorted_indices:
        if len(recommendations) >= total_recs:
            break
        recommendations.append({
            'title': titles[idx],
            'artist': artists_names[idx],
            'similarity': float(similarities[idx])
        })
    
    print(f"✓ Generated {len(recommendations)} recommendations")
    return recommendations


# -------------------------------------------------------------------
# Spotify Playlist Creation
# -------------------------------------------------------------------
def get_track_uri(sp, track_title, artist_name=None):
    """Search Spotify for track URI"""
    query = f"track:{track_title}"
    if artist_name:
        query += f" artist:{artist_name}"
    results = sp.search(q=query, type='track', limit=1)
    if results['tracks']['items']:
        return results['tracks']['items'][0]['uri']
    return None


def create_spotify_playlist(sp, artist, song, song_count, recommendations):
    """Create Spotify playlist with recommendations"""
    user_id = sp.current_user()['id']
    
    # Create playlist
    playlist = sp.user_playlist_create(
        user=user_id,
        name=f"{artist} - {song} Mix",
        public=False,
        description=f"AI-generated playlist based on '{song}' by {artist}"
    )
    print(f"✓ Created playlist: {playlist['name']}")
    
    # Add input song first
    input_uri = get_track_uri(sp, song, artist)
    uris_to_add = []
    added_titles = set()
    
    if input_uri:
        uris_to_add.append(input_uri)
        added_titles.add((song.lower(), artist.lower()))
        print(f"✓ Added input song: {song} by {artist}")
    
    # Add recommendations
    for rec in recommendations:
        if len(uris_to_add) >= song_count:
            break
        
        title = rec['title']
        rec_artist = rec['artist']
        
        # Skip duplicates
        if (title.lower(), rec_artist.lower()) in added_titles:
            continue
        
        uri = get_track_uri(sp, title, rec_artist)
        if uri:
            uris_to_add.append(uri)
            added_titles.add((title.lower(), rec_artist.lower()))
            print(f"  + {title} by {rec_artist}")
        else:
            print(f"  - Could not find: {title} by {rec_artist}")
    
    # Add tracks to playlist
    if uris_to_add:
        sp.playlist_add_items(playlist_id=playlist['id'], items=uris_to_add)
        print(f"✓ Added {len(uris_to_add)} tracks to playlist")
    
    return {
        'playlist_id': playlist['id'],
        'playlist_name': playlist['name'],
        'playlist_url': playlist['external_urls']['spotify'],
        'track_count': len(uris_to_add),
        'uris': uris_to_add
    }


# -------------------------------------------------------------------
# DynamoDB Save Functions
# -------------------------------------------------------------------
def save_song_to_dynamodb(datasets_table, track_title, artist_name, features):
    """Save song features to aidj_datasets table"""
    from decimal import Decimal
    import uuid
    
    item = {
        "track_title": track_title,
        "artist_name": artist_name,
    }
    for i, val in enumerate(features):
        item[f"mel_feat_{i}"] = Decimal(str(val))
    
    datasets_table.put_item(Item=item)
    print(f"✓ Saved '{track_title}' to aidj_datasets")


def save_playlist_to_dynamodb(playlists_table, track_title, artist_name, song_count, uris, spotify_playlist_id):
    """Save playlist record to aidj_playlists table"""
    import uuid
    
    item = {
        "playlist_id": str(uuid.uuid4()),
        "track_title": track_title,
        "artist_name": artist_name,
        "song_amount": int(song_count),
        "playlist": uris,
        "spotify_playlist_id": spotify_playlist_id
    }
    
    playlists_table.put_item(Item=item)
    print(f"✓ Saved playlist record to aidj_playlists")


# -------------------------------------------------------------------
# Main Generation Function
# -------------------------------------------------------------------
def generate_playlist(artist, song, song_count, access_token, datasets_table, playlists_table):
    """
    Main function to generate a playlist
    
    Args:
        artist: Artist name
        song: Song title
        song_count: Number of songs to include
        access_token: Spotify access token
        datasets_table: DynamoDB table resource for songs
        playlists_table: DynamoDB table resource for playlists
    
    Returns:
        dict with playlist info or error
    """
    try:
        # Create Spotify client with user's token
        sp = spotipy.Spotify(auth=access_token)
        
        # Step 1: Extract features from input song
        print(f"\n{'='*50}")
        print(f"GENERATING PLAYLIST")
        print(f"  Input: '{song}' by '{artist}'")
        print(f"  Count: {song_count} songs")
        print(f"{'='*50}\n")
        
        new_song_features = process_user_input_song(song, artist)
        if new_song_features is None:
            return {
                'status': 'error',
                'message': f'Could not extract audio features for "{song}" by {artist}. Try a different song.'
            }
        
        # Step 2: Save input song to aidj_datasets
        save_song_to_dynamodb(datasets_table, song, artist, new_song_features)
        
        # Step 3: Load dataset from DynamoDB
        df = load_dataset_from_dynamodb(datasets_table)
        
        # Step 4: Get recommendations
        recommendations = get_recommendations(new_song_features, df, model, song_count)
        
        # Step 5: Create Spotify playlist
        result = create_spotify_playlist(sp, artist, song, song_count, recommendations)
        
        # Step 6: Save playlist record to aidj_playlists
        save_playlist_to_dynamodb(
            playlists_table=playlists_table,
            track_title=song,
            artist_name=artist,
            song_count=song_count,
            uris=result['uris'],
            spotify_playlist_id=result['playlist_id']
        )
        
        print(f"\n{'='*50}")
        print(f"✓ PLAYLIST CREATED SUCCESSFULLY")
        print(f"  URL: {result['playlist_url']}")
        print(f"{'='*50}\n")
        
        return {
            'status': 'ok',
            'message': 'Playlist created successfully!',
            'playlist': result
        }
        
    except Exception as e:
        print(f"Error generating playlist: {e}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'message': str(e),
            'type': type(e).__name__
        }
